//===========================================================================
// comp_2p2z.v —— 2P2Z 数字补偿器（多周期流水 MAC 版）
//----------------------------------------------------------------------------
// 设计来源：03-FPGA设计/2P2Z环路/设计报告-2P2Z-v1.md
//   fc = 7.00 kHz、PM = 82.6°、Q14 定点化几乎无损
//
// ★ 时序演进史（都是实测踩出来的，写下来省得再踩）：
//   v1 单周期组合逻辑      ：WNS = -8.59 ns ✗（5 乘法 + 48 位加法链在一拍）
//   v2 多周期 MAC（宽乘法）: WNS = -3.80 ns ✗（e 先左移 14 位 → 16×42 乘法 ✗ 超出 DSP48 25×18）
//   v3 窄乘法 + 移位后置    ：WNS = -0.49 ns ✗（DSP 用上了 ✓ 但"乘法→加→寄存"仍要 ~5.5 ns）
//   v4 乘法/加法各打一拍（本文件）：每拍只做一件事 ✓ 时序轻松 ✓
//
//   教训：**乘法器操作数宽度决定它能不能进 DSP48（≤25×18）**；
//         进了 DSP 之后"乘完立刻加"在 200 MHz 下仍然偏紧 → 该打拍就打拍
//         （本项目 200 kHz 环路每周期有 5000 个时钟可用 ✓ 完全不必省）
//
// 差分方程（每 PWM 周期算一次，与 ADC 采样同步）—— 与 Python 定点模型逐位等价 ✓：
//   y[n] = b0·e[n] + b1·e[n-1] + b2·e[n-2] - a1·y[n-1] - a2·y[n-2]
//   bsum = B0·e + B1·e1 + B2·e2                       // 窄乘法，进 DSP ✓
//   asum = A1·y1 + A2·y2                              // 同上 ✓
//   yQ   = ((bsum << QN) - asum) >>> QN               // 归一化回 Q14 ★ 别漏 >>>QN
//   yQ   = clamp(yQ, DUTY_MIN<<QN, DUTY_MAX<<QN)      // ★ anti-windup（内部状态也限幅）
//   duty = clamp(yQ >>> QN, DUTY_MIN, DUTY_MAX)
//
// 另两件必备保护：软启动（参考码 0→REF_CODE，约 5 ms）、开环模式固定 DUTY_INIT
// ⚠️ 原型 Gc(s) 自带积分器 → 输出 y 是【占空比绝对值】，不是增量
//===========================================================================
`timescale 1ns / 1ps

module comp_2p2z #(
    parameter integer QN        = 14,
    parameter signed [15:0] B0  =  624,
    parameter signed [15:0] B1  = -1121,
    parameter signed [15:0] B2  =  504,
    parameter signed [15:0] A1  = -22272,
    parameter signed [15:0] A2  =  5888,
    parameter signed [12:0] REF_CODE = 13'sd2453,   // 5V @ 实测分压比 0.354
    parameter integer REF_INC   = 4,
    parameter integer DUTY_MIN  = 100,
    parameter integer DUTY_MAX  = 900,
    parameter integer DUTY_INIT = 200
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        sample_valid,
    input  wire [11:0] adc_code,
    input  wire        enable,
    output reg  [10:0] duty,
    output reg         done,
    output reg         sat_hi,
    output reg         sat_lo,
    output reg  [12:0] ref_ss
);

    localparam S_IDLE = 4'd0, S_P0 = 4'd1, S_P1 = 4'd2, S_P2 = 4'd3,
               S_P3   = 4'd4, S_P4 = 4'd5, S_SUM = 4'd6, S_SUM2 = 4'd7,
               S_FIN  = 4'd8, S_OUT = 4'd9;

    reg signed [12:0] e1, e2;                    // 误差历史（ADC 码）
    reg signed [24:0] yQ1, yQ2;                  // 输出历史（Q14；duty≤1024 → 25 位够，保证进 DSP）

    reg  [3:0]         st;
    reg  signed [30:0] p0, p1, p2;               // B 侧乘积
    reg  signed [42:0] p3, p4;                   // A 侧乘积
    reg  signed [31:0] bsum;                     // p0+p1+p2
    reg  signed [43:0] asum;                     // p3+p4
    reg  signed [47:0] yQ_raw;                   // 归一化后的 yQ（Q14）
    reg  signed [12:0] e_r;

    wire signed [12:0] e_now = $signed({1'b0, ref_ss}) - $signed({1'b0, adc_code});

    wire signed [47:0] YQ_HI = $signed(DUTY_MAX) <<< QN;
    wire signed [47:0] YQ_LO = $signed(DUTY_MIN) <<< QN;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= S_IDLE;
            p0 <= 31'sd0; p1 <= 31'sd0; p2 <= 31'sd0; p3 <= 43'sd0; p4 <= 43'sd0;
            bsum <= 32'sd0; asum <= 44'sd0; yQ_raw <= 48'sd0; e_r <= 13'sd0;
            e1 <= 13'sd0; e2 <= 13'sd0;
            yQ1 <= $signed(DUTY_INIT) <<< QN;
            yQ2 <= $signed(DUTY_INIT) <<< QN;
            duty <= DUTY_INIT[10:0];
            done <= 1'b0; sat_hi <= 1'b0; sat_lo <= 1'b0;
            ref_ss <= 13'sd0;
        end else begin
            done <= 1'b0;

            if (!enable) begin
                st   <= S_IDLE;
                duty <= DUTY_INIT[10:0];
                yQ1  <= $signed(DUTY_INIT) <<< QN;
                yQ2  <= $signed(DUTY_INIT) <<< QN;
                e1   <= 13'sd0; e2 <= 13'sd0;
                sat_hi <= 1'b0; sat_lo <= 1'b0;
            end else begin
                case (st)
                    S_IDLE: if (sample_valid) begin
                        e_r <= e_now;
                        st  <= S_P0;
                    end
                    // ---- 连续 5 拍：每拍一个乘法（都在 DSP 里，路径短 ✓）
                    S_P0: begin p0 <= $signed(B0) * $signed(e_r);  st <= S_P1; end
                    S_P1: begin p1 <= $signed(B1) * $signed(e1);   st <= S_P2; end
                    S_P2: begin p2 <= $signed(B2) * $signed(e2);   st <= S_P3; end
                    S_P3: begin p3 <= $signed(A1) * yQ1;           st <= S_P4; end
                    S_P4: begin p4 <= $signed(A2) * yQ2;           st <= S_SUM; end
                    // ---- 两对加法（互不相关，路径短 ✓）
                    S_SUM: begin
                        bsum <= p0 + p1;
                        asum <= p3 + p4;
                        st   <= S_SUM2;
                    end
                    S_SUM2: begin
                        bsum <= bsum + p2;
                        st   <= S_FIN;
                    end
                    // ---- 移位相减 + 归一化
                    S_FIN: begin
                        yQ_raw <= (($signed(bsum) <<< QN) - asum) >>> QN;
                        st     <= S_OUT;
                    end
                    // ---- 双重限幅 + 更新状态 + 软启动
                    S_OUT: begin
                        begin : clamp_blk
                            reg signed [47:0] yQ_cl, duty_raw;
                            yQ_cl = (yQ_raw > YQ_HI) ? YQ_HI :
                                    (yQ_raw < YQ_LO) ? YQ_LO : yQ_raw;
                            duty_raw = yQ_cl >>> QN;
                            // ★ yQ_cl 已限幅到 [YQ_LO, YQ_HI] = [DUTY_MIN, DUTY_MAX]<<QN
                            //   故 duty_raw 必在 [DUTY_MIN, DUTY_MAX] 内 ✓ 这里不再重复限幅
                            //   （去掉重复的 11 位比较器链 → 缩短 WNS 违例路径）
                            duty   <= duty_raw[10:0];
                            sat_hi <= (yQ_raw > YQ_HI);
                            sat_lo <= (yQ_raw < YQ_LO);
                            yQ2    <= yQ1;
                            yQ1    <= yQ_cl[24:0];
                        end
                        e2 <= e1;
                        e1 <= e_r;
                        if (ref_ss < REF_CODE)
                            ref_ss <= (ref_ss + REF_INC > REF_CODE) ? REF_CODE
                                                                    : ref_ss + REF_INC;
                        done <= 1'b1;
                        st   <= S_IDLE;
                    end
                    default: st <= S_IDLE;
                endcase
            end
        end
    end

endmodule
