//======================================================================
// tb_dpwm.v —— DPWM 自检测试台（对上板版 dpwm_core 的回归验收）
//----------------------------------------------------------------------
// 不用看波形也能知道过没过：每条检查自己打印 [ OK ] / [FAIL]，最后给总结。
// 五条验收：周期 / 分辨率 / 死区 / 互补 / 故障封锁
// 参数与上板版一致：PERIOD_CY=1000（200 kHz）、DEAD_CY=40（200 ns）
//======================================================================
`timescale 1ns / 1ps

module tb_dpwm;

    // ---- 与被测模块保持一致的参数 ----
    localparam integer PERIOD_CY = 1000;              // 5 us 周期
    localparam integer DEAD_CY   = 40;                // 200 ns 死区（与上板版一致）
    localparam real    TCLK      = 5.0;               // 200 MHz 时钟周期
    localparam real    TSW       = PERIOD_CY * TCLK;  // 5000 ns
    localparam real    TDEAD     = DEAD_CY   * TCLK;  // 200 ns
    localparam real    TOL       = 0.01;              // 时间比较容差（ns）

    reg        clk   = 1'b0;
    reg        rst_n = 1'b0;
    reg        fault = 1'b0;
    reg [10:0] duty  = 11'd0;

    wire pwm_h, pwm_l, period_tick;

    integer errors    = 0;
    integer shoot_cnt = 0;

    real t_a, t_b, meas;
    real h_d500, h_d501, l_d500;

    //------------------------------------------------------------------
    // 被测模块
    //------------------------------------------------------------------
    dpwm_core #(
        .PERIOD_CY (PERIOD_CY),
        .DEAD_CY   (DEAD_CY),
        .DUTY_W    (11)
    ) dut (
        .clk         (clk),
        .rst_n       (rst_n),
        .duty_i      (duty),
        .fault_i     (fault),
        .pwm_h       (pwm_h),
        .pwm_l       (pwm_l),
        .period_tick (period_tick)
    );

    // 200 MHz 时钟
    always #(TCLK/2.0) clk = ~clk;

    //------------------------------------------------------------------
    // 全程监视：任何瞬间两路同时为高都要报错（这是硬件红线）
    //------------------------------------------------------------------
    always @(pwm_h or pwm_l) begin
        if (pwm_h && pwm_l) begin
            shoot_cnt = shoot_cnt + 1;
            $display("[FAIL] 直通短路！t = %0t ns：pwm_h 与 pwm_l 同时为高", $time);
        end
    end

    //------------------------------------------------------------------
    // 主流程
    //------------------------------------------------------------------
    initial begin
        $display("======================================================");
        $display(" DPWM 验收测试台  |  周期 %0.0f ns  |  死区 %0.0f ns", TSW, TDEAD);
        $display("======================================================");

        // ---- 复位 ----
        rst_n = 1'b0; duty = 11'd500; fault = 1'b0;
        repeat (10) @(posedge clk);
        rst_n = 1'b1;
        repeat (5)  @(posedge clk);

        //--------------------------------------------------
        // 验收 1：开关周期 = 5000 ns（200 kHz）
        //--------------------------------------------------
        @(posedge period_tick); t_a = $realtime;
        @(posedge period_tick); t_b = $realtime;
        meas = t_b - t_a;
        if (meas > TSW + TOL || meas < TSW - TOL) begin
            errors = errors + 1;
            $display("[FAIL] 验收1 开关周期：实测 %0.2f ns，应为 %0.0f ns", meas, TSW);
        end else begin
            $display("[ OK ] 验收1 开关周期：%0.2f ns  →  开关频率 %0.1f kHz", meas, 1.0e6/meas);
        end

        //--------------------------------------------------
        // 验收 2：分辨率 —— duty 加 1，高电平时间正好加 5 ns
        //   注意：绝对高电平时间 = (duty - 死区) × 5 ns，死区占的那 40 个计数算“低”
        //--------------------------------------------------
        duty = 11'd500;
        @(posedge pwm_h); t_a = $realtime;
        @(negedge pwm_h); t_b = $realtime;
        h_d500 = t_b - t_a;

        duty = 11'd501;
        @(posedge pwm_h); t_a = $realtime;
        @(negedge pwm_h); t_b = $realtime;
        h_d501 = t_b - t_a;

        meas = h_d501 - h_d500;
        $display("       实测高电平：duty=500 → %0.2f ns；duty=501 → %0.2f ns", h_d500, h_d501);
        if (meas > TCLK + TOL || meas < TCLK - TOL) begin
            errors = errors + 1;
            $display("[FAIL] 验收2 分辨率：duty+1 使高电平变化 %0.2f ns，应为 %0.1f ns", meas, TCLK);
        end else begin
            $display("[ OK ] 验收2 分辨率：duty+1 → 高电平 +%0.2f ns（正好 1 个时钟）", meas);
        end

        //--------------------------------------------------
        // 验收 3：死区 = 200 ns（上管关→下管开，以及反方向，两个都要量）
        //--------------------------------------------------
        duty = 11'd500;
        @(posedge pwm_h);                        // 对齐：上管刚导通
        @(negedge pwm_h); t_a = $realtime;       // 上管关断
        @(posedge pwm_l); t_b = $realtime;       // 下管导通
        meas = t_b - t_a;
        if (meas > TDEAD + TOL || meas < TDEAD - TOL) begin
            errors = errors + 1;
            $display("[FAIL] 验收3 死区（上管关→下管开）：实测 %0.2f ns，应为 %0.0f ns", meas, TDEAD);
        end else begin
            $display("[ OK ] 验收3 死区（上管关 → 下管开）：%0.2f ns", meas);
        end

        @(negedge pwm_l); t_a = $realtime;       // 下管关断
        @(posedge pwm_h); t_b = $realtime;       // 上管导通
        meas = t_b - t_a;
        if (meas > TDEAD + TOL || meas < TDEAD - TOL) begin
            errors = errors + 1;
            $display("[FAIL] 验收3 死区（下管关→上管开）：实测 %0.2f ns，应为 %0.0f ns", meas, TDEAD);
        end else begin
            $display("[ OK ] 验收3 死区（下管关 → 上管开）：%0.2f ns", meas);
        end

        //--------------------------------------------------
        // 验收 4：互补关系 —— 上管高 + 下管高 + 2×死区 = 一个周期
        //--------------------------------------------------
        duty = 11'd500;
        @(posedge pwm_h);   t_a = $realtime;
        @(negedge pwm_h);   h_d500 = $realtime - t_a;
        @(posedge pwm_l);   t_a = $realtime;
        @(negedge pwm_l);   l_d500 = $realtime - t_a;

        meas = h_d500 + l_d500 + 2.0*TDEAD;
        if (meas > TSW + TOL || meas < TSW - TOL) begin
            errors = errors + 1;
            $display("[FAIL] 验收4 互补关系：上管%0.2f + 下管%0.2f + 2×死区(=2×%0.0f) = %0.2f ns，应为 %0.0f ns",
                     h_d500, l_d500, TDEAD, meas, TSW);
        end else begin
            $display("[ OK ] 验收4 互补关系：上管 %0.2f + 下管 %0.2f + 2×死区(=2×%0.0f) = %0.2f ns",
                     h_d500, l_d500, TDEAD, meas);
        end

        //--------------------------------------------------
        // 验收 5：故障封锁 —— fault_i 拉高，两路立刻为低
        //--------------------------------------------------
        duty = 11'd500; fault = 1'b0;
        repeat (3) @(posedge clk);
        fault = 1'b1;
        @(posedge clk); #1;
        if (pwm_h !== 1'b0 || pwm_l !== 1'b0) begin
            errors = errors + 1;
            $display("[FAIL] 验收5 故障封锁：fault_i=1 时仍有输出（pwm_h=%b pwm_l=%b）", pwm_h, pwm_l);
        end else begin
            $display("[ OK ] 验收5 故障封锁：fault_i=1 → 两路同时为低");
        end
        fault = 1'b0;
        repeat (10) @(posedge clk);

        //--------------------------------------------------
        // 总结
        //--------------------------------------------------
        $display("------------------------------------------------------");
        if (errors == 0 && shoot_cnt == 0) begin
            $display(" 结果：全部通过   验收 1-5 达标，可以截图存档");
        end else begin
            $display(" 结果：失败   errors = %0d  直通次数 = %0d", errors, shoot_cnt);
        end
        $display("------------------------------------------------------");
        $finish;
    end

endmodule
