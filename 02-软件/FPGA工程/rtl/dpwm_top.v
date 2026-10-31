//===========================================================================
// dpwm_top.v —— 顶层 wrapper（10/9 上板 bring-up 用）
//----------------------------------------------------------------------------
// 结构：
//   1) 时钟：板载 50 MHz → Clocking Wizard(clk_wiz_0) → 200 MHz + locked
//   2) 复位：板载按键 & locked（MMCM 没锁死之前整体保持复位）
//   3) 故障：FAULT_N → 2FF 同步 → 原始故障(protect_raw) → 一路接 DPWM 逐周期封锁
//                                                       → 一路闩锁后驱动 SD
//   4) 冻结的 DPWM 核 dpwm_core（v1，接口冻结在 ..\骨架和testbench\dpwm_core.v）
//   5) ADC 采样时钟：200 MHz ÷ 100 = 2 MHz（与 DPWM 计数器同源 → 相位固定）
//   6) ILA 预留（6 探针，生成 IP 后取消注释）
//----------------------------------------------------------------------------
// 与 2026-10-08 B 线评审意见的对应：
//   * 网名 SD_EN → SD（与 IR2110 引脚同名，消灭歧义）；极性见下面的真值表
//   * 增加 2FF 同步器（fault_n 是异步输入，跨时钟域必加）
//   * DPWM 逐周期封锁用【原始】故障；驱动关断用【闩锁】故障 —— 两级保护
//   * ADC_CLK 由 FPGA 提供（PWM 同步采样的前提），2 MHz
//----------------------------------------------------------------------------
// 本文件里【故意不写引脚号】——引脚只出现在 XDC 里，等板卡资料盘。
//===========================================================================
`timescale 1ns / 1ps

module dpwm_top (
    input  wire clk_50m,      // 板载 50 MHz 晶振（引脚待填）
    input  wire rst_btn_n,    // 核心板板载按键，低有效（bring-up 不依赖 PS）
    input  wire FAULT_N,      // LM393 开集 + 3.3V 上拉：0 = 过流（低有效）
    input  wire [11:0] adc_d, // AD9226 数据：adc_d[0] = LSB ← 模块 BIT12（接反不报错、读数全乱！）
    input  wire adc_otr,      // AD9226 超量程标志（高有效）
    input  wire loop_en,      // ★ 闭环使能：1 = 2P2Z 控制占空比；0 = 固定 BRINGUP_DUTY
    input  wire adc_inv_off, // ADC 取反禁能: 0=取反(默认,内部下拉) 1=不取反  -- J10 第21针 V18
                              //   XDC 里配 PULLDOWN → 上电默认【开环】，特意接高才闭环 ✓ 安全
    output wire pwm_h,        // → 74HCT245 → IR2110 HIN   （245 A 侧 10k 下拉）
    output wire pwm_l,        // → 74HCT245 → IR2110 LIN   （245 A 侧 10k 下拉）
    output wire SD,           // → IR2110 SD 脚：0 = 正常，1 = 关断（A 侧 10k 下拉）
    output wire ADC_CLK,      // → AD9226 CLK：2 MHz（200 MHz ÷ 100）
    output wire led,          // 板载 LED：约 1 Hz 心跳（上板第一眼看它闪不闪）
    output wire pwm_tick      // period_tick（接 ILA / 测试点）
);

    //------------------------------------------------------------------------
    // 0) 占空比来源：闭环（2P2Z）或开环固定值
    //    loop_en = 0（XDC 配 PULLDOWN，上电默认）→ 固定 BRINGUP_DUTY ✓ 安全
    //    loop_en = 1 → 由 comp_2p2z 控制（软启动 + 限幅 + anti-windup ✓）
    //------------------------------------------------------------------------
    parameter integer BRINGUP_DUTY = 200;      // 200 × 5 ns = 1000 ns，约 20%
    wire [10:0] duty_from_comp;
    wire [10:0] duty_used = loop_en ? duty_from_comp : BRINGUP_DUTY[10:0];

    //------------------------------------------------------------------------
    // 1) 时钟：50 MHz → 200 MHz
    //    clk_wiz_0 由 Vivado IP Catalog 生成（10/9，设置见 README）；
    //    仿真时用 clk_wiz_0_sim.v 顶替，端口一致。
    //------------------------------------------------------------------------
    wire clk_200m;
    wire mmcm_locked;

    clk_wiz_0 u_clk_wiz (
        .clk_in1  (clk_50m),
        .reset    (1'b0),
        .clk_out1 (clk_200m),
        .locked   (mmcm_locked)
    );

    // 时钟没锁之前保持复位：否则上电瞬间会输出没意义的脉宽
    wire rst_n = rst_btn_n & mmcm_locked;

    //------------------------------------------------------------------------
    // 2) 故障输入：2FF 同步器
    //    FAULT_N 来自板上的 LM393（开集 + 3.3V 上拉），对 FPGA 是**异步**信号，
    //    直接进逻辑会有亚稳态风险，所以先过两级触发器。
    //    复位值取 2'b11（= 无故障），避免上电误闩锁；2 拍就同步好了，
    //    而 v1 因为有死区、要 4~5 拍才出第一个脉冲，所以复位释放时不会漏判。
    //    SD 真值表（IR2110 原厂手册：SD 高电平封波，内部下拉，悬空=使能）：
    //        SD = 0 → 正常，HO/LO 受 HIN/LIN 控制
    //        SD = 1 → 关断，HO = LO = 0
    //------------------------------------------------------------------------
    reg [1:0] sync_ff;

    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n) sync_ff <= 2'b11;
        else        sync_ff <= {sync_ff[0], FAULT_N};
    end

    // ★ 数字滤波：连续 FILT_CYC 拍为低才认定故障（滤掉纪元级毛刺）
    localparam integer FILT_CYC  = 200;    // 200 x 5ns = 1 us（滤掉偶发毛刺）
    localparam integer BLANK_BITS = 19;    // 2^19 x 5ns = 2.62 ms 上电消隐
    reg [7:0] fault_low_cnt;
    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n)                  fault_low_cnt <= 8'd0;
        else if (sync_ff[1])         fault_low_cnt <= 8'd0;      // 高电平清零
        else if (fault_low_cnt != 8'd255) fault_low_cnt <= fault_low_cnt + 1'b1;
    end
    wire fault_filtered = (fault_low_cnt >= FILT_CYC[7:0]);

    reg [BLANK_BITS-1:0] blank_cnt;
    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n) blank_cnt <= {BLANK_BITS{1'b0}};
        else if (blank_cnt != {BLANK_BITS{1'b1}}) blank_cnt <= blank_cnt + 1'b1;
    end
    wire blank_done = (blank_cnt == {BLANK_BITS{1'b1}});

    wire protect_raw = fault_filtered & blank_done;   // 1 = 过流（滤波+消隐后）

    //------------------------------------------------------------------------
    // 3) 两级保护
    //    - 逐周期：protect_raw 直接给 DPWM 的 fault_i，超限即封、下周期重试
    //    - 闩锁  ：protect_latched 驱动 SD，一旦过流就把驱动关到复位为止
    //    注意：闩锁之后 DPWM 仍会继续发 PWM（它按"原始故障"逐周期工作），
    //          但 IR2110 被 SD 关断，HO/LO 恒为低 —— 这是有意设计的，不是 bug。
    //------------------------------------------------------------------------
    reg protect_latched;

    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n)            protect_latched <= 1'b0;
        else if (protect_raw)  protect_latched <= 1'b1;   // 锁住，复位才解除
    end

    // ★★ 调试开关（2026-10-22）：为排查"无输出"而临时旁路保护闸锁。
    //   SD_BYPASS = 1 → 强制 SD = 0（不关断，仅调试用）
    //   SD_BYPASS = 0 → 正常保护（上板前必须改回 0）
    localparam SD_BYPASS = 1'b0;   // 保护开启（滤波 1us + 消隐 2.62ms）
    assign SD = SD_BYPASS ? 1'b0 : protect_latched;   // 0 = 正常，1 = 关断
    wire   fault_i = protect_raw;        // → v1（1 = 封锁）

    //------------------------------------------------------------------------
    // 4) ADC 接口（AD9226）—— 见 adc_if.v
    //    2 MHz 采样时钟由 adc_if 内部产生，并被 pwm_tick 逐周期对齐，
    //    因此采样相位固定；配合 AD9226 的 7 拍流水线延迟，
    //    可通过 LATCH_CYC 把采样点挪到开关周期的"安静窗"里。
    //    ⚠️ 位序：adc_d[0] 必须是 LSB（模块 BIT12）；验证法 0.5 V → 期望 0x400。
    //------------------------------------------------------------------------
    wire [11:0] adc_centered;
    wire        adc_valid, adc_otr_s, adc_otr_sticky;

    adc_if #(
        .DIV       (100),
        .N_CYC     (10),
        .LATCH_CYC (3),          // 实际采样点 = (3-7) mod 10 = 第 6 格（每格 500 ns）
        .LATCH_OFF (60),
        .PIPE_CY   (7),
        .WARMUP    (16),
        .MID_CODE  (12'h800)
    ) u_adc (
        .clk        (clk_200m),
        .rst_n      (rst_n),
        .pwm_tick   (pwm_tick),
        .adc_d      (adc_d),
        .adc_otr    (adc_otr),
        .adc_clk    (ADC_CLK),        // → 模块采样时钟
        .adc_code(adc_code_raw),
        .adc_centered(adc_centered),
        .adc_valid  (adc_valid),
        .adc_otr_s  (adc_otr_s),
        .adc_otr_sticky(adc_otr_sticky)
    );

    //------------------------------------------------------------------------
    // 4·补) 2P2Z 补偿器（闭环）—— 见 comp_2p2z.v
    //    设计：fc = 7.00 kHz、PM = 82.6°（详见 03-FPGA设计/2P2Z环路/设计报告-2P2Z-v1.md）
    //    系数 Q14：B0=624  B1=-1121  B2=504  A1=-22272  A2=5888
    //    ★ 内含：软启动（~5 ms）、输出限幅 [100,900]、anti-windup（内部状态一起限幅）
    //    RTL 已与 Python 定点模型逐点对拍（1100 点，零失配 ✓）
    //------------------------------------------------------------------------
    wire        comp_sat_hi, comp_sat_lo;
    wire [12:0] comp_ref_ss;
    // ★ 运行时取反 (跳线可选): 0=取反(默认) 1=不取反
    // ★ 取反寄存一拍（避免打乱 ADC→补偿器 的时序）
    //    adc_valid 同步延一拍，保持与码值对齐
    // ★ v3：最简直读方案（绕过 adc_if 的窄窗口锁存）
    //   ADC 在 2 MHz 下数据稳定 500 ns → 不需要精确相位
    //   每个 PWM 周期固定延时 200 拍（1 µs）后采一次
    //  ★ 采样三点 = 220/250/280 拍（间隔 150 ns）：ADC_CLK 每 100 拍一个上升沿，
    //     200 拍正好压在数据跳变上✷ → 改为周期正中的 250 拍 ✓
    reg  [11:0] adc_code;
    reg         adc_valid_d;
    reg  [9:0]  adc_dly;
    reg  [11:0] s1, s2, s3;
    wire [11:0] s0 = adc_inv_off ? ~adc_d : adc_d;
    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n) begin
            adc_code <= 12'd0; adc_valid_d <= 1'b0; adc_dly <= 10'd0; s1 <= 12'd0; s2 <= 12'd0; s3 <= 12'd0;
        end else begin
            adc_dly <= pwm_tick ? 10'd0 : adc_dly + 1'b1;
            // ★ v5：三点采样 + 3取2 多数表决，消除单点毛刺
            if (adc_dly == 10'd220) s1 <= adc_inv_off ? ~adc_d : adc_d;
            if (adc_dly == 10'd250) s2 <= adc_inv_off ? ~adc_d : adc_d;
            if (adc_dly == 10'd280) s3 <= adc_inv_off ? ~adc_d : adc_d;
            if (adc_dly == 10'd281) begin
                adc_code    <= s1 & s2 | s1 & s3 | s2 & s3;   // 逐位三取二（全为寄存器 ✓）
                adc_valid_d <= 1'b1;
            end else begin
                adc_valid_d <= 1'b0;
            end
        end
    end


    comp_2p2z #(
        .QN        (14),
        .B0        (624), .B1(-1121), .B2(504), .A1(-22272), .A2(5888),
        .REF_CODE  (13'sd2453),      // 5 V 对应的 ADC 码（外部分压 0.2017）
        .REF_INC   (4),              // 软启动：3994/4 × 5µs ≈ 5 ms
        .DUTY_MIN  (100),
        .DUTY_MAX  (900),
        .DUTY_INIT (200)
    ) u_comp (
        .clk          (clk_200m),
        .rst_n        (rst_n),
        .sample_valid(adc_valid_d),   // 与 ADC 采样同步，每 PWM 周期算一次
        .adc_code     (adc_code),
        .enable       (loop_en),
        .duty         (duty_from_comp),
        .sat_hi       (comp_sat_hi),
        .sat_lo       (comp_sat_lo),
        .ref_ss       (comp_ref_ss)
    );

    //------------------------------------------------------------------------
    // 4·补) 心跳 LED：约 1 Hz 闪烁
    //    上板第一件事就是看它闪——灯闪说明"时钟 + 配置 + 工具链"全通，
    //    再把示波器夹到 pwm_h 上，才轮到看设计对不对。
    //    ⚠️ AX7020 的 LED 可能是**低电平点亮**（以原理图为准）；若反了，把 assign 取反。
    //------------------------------------------------------------------------
    parameter integer HEARTBEAT_DIV = 100_000_000;   // 200 MHz ÷ 1e8 → 每 0.5 s 翻转
    reg [31:0] hb_cnt;
    reg        hb_led;

    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n) begin
            hb_cnt <= 32'd0;
            hb_led <= 1'b0;
        end else if (hb_cnt >= HEARTBEAT_DIV - 1) begin
            hb_cnt <= 32'd0;
            hb_led <= ~hb_led;
        end else begin
            hb_cnt <= hb_cnt + 1'b1;
        end
    end

    assign led = hb_led;      // 若板上 LED 低电平点亮 → assign led = ~hb_led;

    //------------------------------------------------------------------------
    // 5) 冻结的 DPWM 核（v1）—— 一个字都没改，只在外面接信号
    //------------------------------------------------------------------------
    dpwm_core #(
        .PERIOD_CY (1000),      // 200 kHz（周期 5000 ns）
        .DEAD_CY   (40),        // 200 ns（功率级 BOM 要求的死区）
        .DUTY_W    (11)
    ) u_dpwm (
        .clk         (clk_200m),
        .rst_n       (rst_n),
        .duty_i      (duty_used),
        .fault_i     (fault_i),
        .pwm_h       (pwm_h),
        .pwm_l       (pwm_l),
        .period_tick (pwm_tick)
    );

    //------------------------------------------------------------------------
    // 6) 保护响应时间监测（bring-up 诊断，最终版本可删）
    //    量什么：FAULT_N 引脚下降沿 → 两路 PWM 都封住（且同步故障已到）的时间
    //    精度  ：clk_200m = 5 ns/步；预期 ≈2~3 步（10~15 ns）
    //            理论：2FF 同步 2 拍 = 10 ns + 核内寄存封锁 1 拍 = 5 ns
    //    读法  ：resp_lat 送到 ILA 的 probe5（原本是 duty_used[10:0]，本版临时占用）
    //            字段 = {resp_n[2:0], resp_lat[7:0]}：低 8 位是最近一次响应步数
    //------------------------------------------------------------------------
    reg  [7:0]  resp_cnt;
    reg  [7:0]  resp_first;     // ★ 复位后第一次测得的响应（冻结，不被后续覆盖）
    reg  [1:0]  resp_n;
    reg         resp_run, resp_got, fault_pin_d;

    wire fault_pin  = ~FAULT_N;                           // 引脚上异步的原始故障（高有效）
    wire blanked    = (~(pwm_h | pwm_l)) & protect_raw;   // 两路都低 且 同步故障已到
    wire fault_edge = fault_pin & ~fault_pin_d;           // ★ 只在"下降沿"启动，
                                                          //   否则故障持续保持时会反复重启、把真值覆盖成 0

    always @(posedge clk_200m or negedge rst_n) begin
        if (!rst_n) begin
            resp_cnt <= 8'd0; resp_first <= 8'd0; resp_n <= 2'd0;
            resp_run <= 1'b0; resp_got <= 1'b0; fault_pin_d <= 1'b0;
        end else begin
            fault_pin_d <= fault_pin;
            if (fault_edge) begin
                resp_run <= 1'b1; resp_cnt <= 8'd0;       // 新故障 → 开始计时
            end else if (resp_run) begin
                if (blanked) begin                        // 已封波 → 记录
                    resp_run <= 1'b0;
                    resp_n   <= resp_n + 1'b1;
                    if (!resp_got) begin
                        resp_first <= resp_cnt;           // ★ 第一次的值冻结保存
                        resp_got   <= 1'b1;
                    end
                end else if (resp_cnt != 8'hFF) begin
                    resp_cnt <= resp_cnt + 1'b1;
                end
            end
        end
    end

    // 11 位对接 ILA probe5：{got, n[1:0], first[7:0]}
    wire [10:0] resp_probe = {resp_got, resp_n, resp_first};

    //------------------------------------------------------------------------
    // 7) ILA（板内逻辑分析仪）
    //    10/9 在 Vivado 里生成 ila_0 之后，取消下面的注释再综合。
    //    探针宽度：1+1+1+1+1+11，生成时按这个顺序配。
    //------------------------------------------------------------------------
    // ila_0 u_ila (
    //     .clk    (clk_200m),
    //     .probe0 (pwm_h),           // 1
    //     .probe1 (pwm_l),           // 1
    //     .probe2 (pwm_tick),        // 1
    //     .probe3 (fault_i),         // 1
    //     .probe4 (SD),              // 1
    //     .probe5 (duty_used)        // 11
    // );
    // ↑ 10/10 已改为启用（片内测量死区用）：
    ila_0 u_ila (
        .clk    (clk_200m),
        .probe0 (pwm_h),           // 1
        .probe1 (pwm_l),           // 1
        .probe2 (pwm_tick),        // 1
        .probe3 (fault_i),         // 1
        .probe4 (adc_code[11]),              // 1
        .probe5 (adc_code[10:0])   // 11  ← ADC 低 11 位（配合 probe4 拼 12 位）
                                   //      0.5V 应对应 0x400；若读到 0x002 则位序整体反了
                                   //      （闭环诊断位段 {sat_hi,sat_lo,loop_en,duty[7:0]} 已在
                                   //        10/12 用过并验证通过，需要时换回即可）
    );

endmodule
