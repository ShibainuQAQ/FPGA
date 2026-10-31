//======================================================================
// dpwm_core.v —— 高分辨率 DPWM 核心（第一版：粗计数器 + 死区 + 互补输出）
//----------------------------------------------------------------------
// 项目：FPGA 高分辨率数字电源控制器（2026 嵌入式竞赛 FPGA 赛道）
// 角色：A 线（PL 主力）10/7 W2 验收靶子
//
// 【它做什么】
//   1) 用计数器数 200 MHz 时钟，每 1000 个数 = 一个开关周期（5 us = 200 kHz）
//   2) 计数值 < duty_i 时上管"想开"，否则下管"想开"
//   3) 谁要开，必须等另一路关断满 DEAD_CY 个时钟（死区），防止直通
//   4) 任何瞬间两路都不同时为高（同时为高 = 上下管直通 = 电源短路）
//
// 【本版不包含（诚实边界）】
//   - 细延时 IODELAY：本版分辨率 = 1 个时钟 = 5 ns；"亚 ns 级"靠后续细延时实现
//   - 软启动、OCP 比较器：只留了 fault_i 端口
//======================================================================
`timescale 1ns / 1ps

module dpwm_core #(
    parameter integer PERIOD_CY = 1000,   // 开关周期 = 多少个 200 MHz 时钟（1000 → 5 us → 200 kHz）
    parameter integer DEAD_CY   = 40,     // 死区 = 40 个时钟 = 200 ns（IR2110 传输延迟失配 ≈100 ns → 需 ≥200 ns ✓）
    parameter integer DUTY_W    = 11      // 占空比位宽（要能装下 0..PERIOD_CY）
)(
    input  wire              clk,          // 200 MHz 系统时钟
    input  wire              rst_n,        // 低有效复位
    input  wire [DUTY_W-1:0] duty_i,       // 占空比：上管导通的时钟数（0..PERIOD_CY）
    input  wire              fault_i,      // 故障输入：1 = 立刻封锁两路输出
    output reg               pwm_h,        // 上管驱动
    output reg               pwm_l,        // 下管驱动
    output wire              period_tick   // 周期起点脉冲（采样/控制环用，cnt==0 时高一个时钟）
);

    // 死区判据：另一路的"关断计时"要走到这个值，才允许本路开通
    localparam integer DEAD_TH = (DEAD_CY > 0) ? (DEAD_CY - 1) : 0;

    //------------------------------------------------------------------
    // 1) 周期计数器：0 .. PERIOD_CY-1 循环
    //------------------------------------------------------------------
    reg [DUTY_W-1:0] cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= {DUTY_W{1'b0}};
        else if (cnt >= PERIOD_CY - 1)
            cnt <= {DUTY_W{1'b0}};
        else
            cnt <= cnt + 1'b1;
    end

    assign period_tick = (cnt == {DUTY_W{1'b0}});

    //------------------------------------------------------------------
    // 2) 理想导通区间（还没考虑死区）
    //------------------------------------------------------------------
    wire h_want = (cnt <  duty_i);    // 上管理想上导通
    wire l_want = (cnt >= duty_i);    // 下管理想上导通（与上管理想互补）

    //------------------------------------------------------------------
    // 3) 死区计时：记录"另一路已经关断了多少个时钟"
    //    某一路为高 → 它的关断计时清零；为低 → 每个时钟 +1（到 DEAD_CY 封顶）
    //------------------------------------------------------------------
    reg [DUTY_W-1:0] h_off_cnt;   // 上管已关断的时钟数
    reg [DUTY_W-1:0] l_off_cnt;   // 下管已关断的时钟数

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_off_cnt <= {DUTY_W{1'b0}};
            l_off_cnt <= {DUTY_W{1'b0}};
        end else if (fault_i) begin
            h_off_cnt <= {DUTY_W{1'b0}};
            l_off_cnt <= {DUTY_W{1'b0}};
        end else begin
            h_off_cnt <= pwm_h ? {DUTY_W{1'b0}}
                               : ((h_off_cnt < DEAD_CY) ? (h_off_cnt + 1'b1) : h_off_cnt);
            l_off_cnt <= pwm_l ? {DUTY_W{1'b0}}
                               : ((l_off_cnt < DEAD_CY) ? (l_off_cnt + 1'b1) : l_off_cnt);
        end
    end

    //------------------------------------------------------------------
    // 4) 输出寄存器：想开 且 另一路已关断够久 → 才允许开
    //    想关 → 立刻关（关断永远不延迟）
    //------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_h <= 1'b0;
            pwm_l <= 1'b0;
        end else if (fault_i) begin
            pwm_h <= 1'b0;        // 故障：无条件封锁
            pwm_l <= 1'b0;
        end else begin
            pwm_h <= h_want & (l_off_cnt >= DEAD_TH);
            pwm_l <= l_want & (h_off_cnt >= DEAD_TH);
        end
    end

endmodule
