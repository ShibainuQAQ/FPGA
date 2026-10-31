//===========================================================================
// adc_if.v —— AD9226 采样接口（PWM 周期同步 / 安静窗采样）
//----------------------------------------------------------------------------
// 依赖：clk = 200 MHz（与 DPWM 同源），pwm_tick = 每个 PWM 周期起始 1 拍
// 产出：adc_clk（2 MHz → 模块）、adc_code（原始 offset binary 12 位）、
//       adc_centered（减中点后的值，给环路）、adc_valid（每 PWM 周期 1 拍）、
//       adc_otr_s（本次超量程）、adc_otr_sticky（历史发生过，复位才清）
//
// 【一、位序 —— 最容易错的地方】
//   AD9226 模块上的引脚命名与"位号"是反着数的：
//       BIT 12 = LSB（模块第 2 脚）   BIT 1 = MSB（模块第 13 脚）
//   本模块的 adc_d[0] 就是【LSB】→ 接线时必须：
//       adc_d[0] ← 模块 BIT 12（LSB），adc_d[11] ← 模块 BIT 1（MSB）
//   验证法：输入 0.5 V，期望读数 ≈ 0x400；若读到 ≈ 0x002，说明位序整体反了。
//
// 【二、采样时刻 —— 流水线延迟】
//   AD9226 是流水线 ADC：数据在采样边沿之后 PIPE_CY(7) 个时钟才出现在总线上。
//   所以"在第 LATCH_CYC 个 ADC 周期锁存数据"= 实际采样发生在
//       第 (LATCH_CYC - PIPE_CY) mod N_CYC 个 ADC 周期
//   例如 LATCH_CYC=3、PIPE_CY=7、N_CYC=10 → 实际采样在【第 6 个】ADC 周期
//   （一个 PWM 周期 5 µs 共 10 个 ADC 周期，每格 500 ns）。
//   改 LATCH_CYC 就能把采样点挪到安静窗里（上板后按波形调）。
//
// 【三、为什么和 PWM 同步】
//   adc_div / adc_cyc 都被 pwm_tick 重新对齐，且 1 个 PWM 周期 = 整数个
//   (10 个) ADC 周期 → 每格的相位固定，采样点每周期都落在同一个位置 ✓
//===========================================================================
`timescale 1ns / 1ps

module adc_if #(
    parameter integer DIV        = 100,      // 200 MHz / 100 = 2 MHz
    parameter integer N_CYC      = 10,       // 每个 PWM 周期内的 ADC 时钟个数
    parameter integer LATCH_CYC  = 3,        // 在第几个 ADC 周期锁存数据
    parameter integer LATCH_OFF  = 60,       // 该周期内第几拍锁存（避开模块输出翻转）
    parameter integer PIPE_CY    = 7,        // AD9226 流水线延迟（手册值）
    parameter integer WARMUP     = 16,       // 上电后忽略前 N 次采样（流水线未填满）
    parameter [11:0]  MID_CODE   = 12'h800   // 中点码（0 A / 0 V 对应的码，按模块偏置调）
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        pwm_tick,        // PWM 周期起始脉冲（1 拍）
    input  wire [11:0] adc_d,           // AD9226 数据（adc_d[0] = LSB）
    input  wire        adc_otr,         // 超量程标志（高有效）
    output wire        adc_clk,         // → 模块采样时钟（2 MHz，50% 占空比）
    output reg  [11:0] adc_code,        // 原始码（offset binary）
    output reg  [11:0] adc_centered,    // 去中点（有符号量按 13 位看）
    output reg         adc_valid,       // 每次有效采样 1 拍（200 kHz）
    output reg         adc_otr_s,       // 本次采样是否超量程
    output reg         adc_otr_sticky   // 历史发生过超量程（复位才清）
);

    //-----------------------------------------------------------------------
    // 1) 2 MHz 采样时钟：每个 PWM 周期重新对齐（保证相位固定）
    //-----------------------------------------------------------------------
    reg [7:0] adc_div;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)                  adc_div <= 8'd0;
        else if (pwm_tick)           adc_div <= 8'd0;          // ★ 周期对齐
        else if (adc_div == DIV-1)   adc_div <= 8'd0;
        else                         adc_div <= adc_div + 1'b1;
    end

    assign adc_clk = (adc_div < (DIV/2)) ? 1'b1 : 1'b0;        // 50% 占空比

    //-----------------------------------------------------------------------
    // 2) ADC 周期序号 0..N_CYC-1
    //-----------------------------------------------------------------------
    reg [3:0] adc_cyc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)                              adc_cyc <= 4'd0;
        else if (pwm_tick)                       adc_cyc <= 4'd0;
        else if (adc_div == DIV-1)
            adc_cyc <= (adc_cyc == N_CYC-1) ? 4'd0 : adc_cyc + 1'b1;
    end

    //-----------------------------------------------------------------------
    // 3) 锁存 + 上电预热
    //-----------------------------------------------------------------------
    wire latch_now = (adc_cyc == LATCH_CYC) && (adc_div == LATCH_OFF);

    reg [5:0] warm_cnt;
    wire      warm_done = (warm_cnt >= WARMUP);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            adc_code       <= 12'd0;
            adc_centered   <= 12'd0;
            adc_valid      <= 1'b0;
            adc_otr_s      <= 1'b0;
            adc_otr_sticky <= 1'b0;
            warm_cnt       <= 6'd0;
        end else begin
            adc_valid <= latch_now & warm_done;

            if (latch_now) begin
                if (!warm_done) begin
                    warm_cnt <= warm_cnt + 1'b1;      // 预热期：只数，不输出
                end else begin
                    adc_code       <= adc_d;          // ★ adc_d[0] = LSB
                    adc_centered   <= adc_d - MID_CODE;
                    adc_otr_s      <= adc_otr;
                    if (adc_otr) adc_otr_sticky <= 1'b1;
                end
            end
        end
    end

endmodule
