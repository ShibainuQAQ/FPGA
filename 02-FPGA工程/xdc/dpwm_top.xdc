#===========================================================================
# dpwm_top.xdc —— AX7020 引脚约束（2026-10-09 用官方资料补全）
#----------------------------------------------------------------------------
# 引脚来源（全部来自 ALINX 官方资料，不是猜的）：
#   1) Hardware/01_SCH/AX7010_AX7020管脚.xlsx —— FPGA 管脚 ↔ 核心板网络名
#   2) course_s1_fpga/01_led/.../led.xdc      —— 官方的时钟/按键/LED 约束写法
#
# 板载固定引脚（官方已确认）：
#   PL 时钟 50 MHz = U18 (网络名 PL_GCLK)     按键 KEY1 = N15
#   LED1..4 = M14 / M15 / K16 / J16
#
# 扩展口：40-pin 排针引出的 PL IO，网络名 IO1_xN/P、IO2_xN/P（共 34 对 = 68 个 IO）
#   ★ 上板接线时请让 B 线**按网络名**在原理图（AX7020开发板原理图V2.0.pdf）
#     里找对应的排针位置——网络名是唯一不会歧义的对照物。
#===========================================================================

#---- 时钟：50 MHz 有源晶振，周期 20 ns -------------------------------------
set_property PACKAGE_PIN U18 [get_ports clk_50m]
set_property IOSTANDARD LVCMOS33 [get_ports clk_50m]
create_clock -period 20.000 -name clk_50m -waveform {0.000 10.000} [get_ports clk_50m]

#---- 复位：板载按键 KEY1（低有效）------------------------------------------
set_property PACKAGE_PIN N15 [get_ports rst_btn_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_btn_n]

#---- 心跳 LED：LED1 -------------------------------------------------------
# 若板载 LED 是低电平点亮，把 dpwm_top.v 里 assign led 取反
set_property PACKAGE_PIN M14 [get_ports led]
set_property IOSTANDARD LVCMOS33 [get_ports led]

#===========================================================================
# 40-pin 扩展口（H 区）—— 网名 → FPGA 管脚
#===========================================================================
# pwm_h    -> IO1_1P
set_property PACKAGE_PIN W18 [get_ports pwm_h]
set_property IOSTANDARD LVCMOS33 [get_ports pwm_h]

# pwm_l    -> IO1_1N
set_property PACKAGE_PIN W19 [get_ports pwm_l]
set_property IOSTANDARD LVCMOS33 [get_ports pwm_l]

# SD       -> IO1_2P   （→ 74HCT245 → IR2110 SD）
set_property PACKAGE_PIN P14 [get_ports SD]
set_property IOSTANDARD LVCMOS33 [get_ports SD]

# FAULT_N  -> IO1_2N   （← LM393 开集 + 3.3V 上拉）
set_property PACKAGE_PIN R14 [get_ports FAULT_N]
set_property IOSTANDARD LVCMOS33 [get_ports FAULT_N]
# ★ 内部上拉：台面单独测试时 IO1_2N 悬空，CMOS 输入电平不确定，
#   读成低会立刻触发保护（PWM 全被封、SD 拉高），看起来像"设计没跑"。
#   功率板接上后 LM393 侧有 10 kΩ 外部上拉，这个内部上拉（≈50 kΩ）只是冗余保险，无害。
set_property PULLUP true [get_ports FAULT_N]

# ADC_CLK  -> IO1_3P   （→ AD9226 CLK，2 MHz）
set_property PACKAGE_PIN Y16 [get_ports ADC_CLK]
set_property IOSTANDARD LVCMOS33 [get_ports ADC_CLK]

# pwm_tick -> IO1_3N   （示波器测试点；只接 ILA 也行，这一针可以不用）
set_property PACKAGE_PIN Y17 [get_ports pwm_tick]
set_property IOSTANDARD LVCMOS33 [get_ports pwm_tick]

#===========================================================================
# ADC 通路（AD9226）—— 2026-10-11 添加
#----------------------------------------------------------------------------
# ★ 位序：adc_d[0] = LSB ← 模块 BIT 12（模块引脚命名与位号反着数，接反不报错！）
#   排针：J10 第 9~20 针 = IO1_4N / 4P / 5N / 5P / 6N / 6P / 7N / 7P / 8N / 8P / 9N / 9P
#         J10 第 22 针 = IO1_10P（OTR）
#   这些球号/针号已在 2026-10-11 逐针扫频**物理确认**
#   （见 02-接口契约/J10排针-全表物理实测确认-20261011.md）
#===========================================================================

# adc_d[0]  -> IO1_4N  (J10 第 9 针)   ← LSB！
set_property PACKAGE_PIN W15 [get_ports {adc_d[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[0]}]

# adc_d[1]  -> IO1_4P  (J10 第 10 针)
set_property PACKAGE_PIN V15 [get_ports {adc_d[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[1]}]

# adc_d[2]  -> IO1_5N  (J10 第 11 针)
set_property PACKAGE_PIN Y14 [get_ports {adc_d[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[2]}]

# adc_d[3]  -> IO1_5P  (J10 第 12 针)
set_property PACKAGE_PIN W14 [get_ports {adc_d[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[3]}]

# adc_d[4]  -> IO1_6N  (J10 第 13 针)
set_property PACKAGE_PIN P18 [get_ports {adc_d[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[4]}]

# adc_d[5]  -> IO1_6P  (J10 第 14 针)
set_property PACKAGE_PIN N17 [get_ports {adc_d[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[5]}]

# adc_d[6]  -> IO1_7N  (J10 第 15 针)
set_property PACKAGE_PIN U15 [get_ports {adc_d[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[6]}]

# adc_d[7]  -> IO1_7P  (J10 第 16 针)
set_property PACKAGE_PIN U14 [get_ports {adc_d[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[7]}]

# adc_d[8]  -> IO1_8N  (J10 第 17 针)
set_property PACKAGE_PIN P16 [get_ports {adc_d[8]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[8]}]

# adc_d[9]  -> IO1_8P  (J10 第 18 针)
set_property PACKAGE_PIN P15 [get_ports {adc_d[9]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[9]}]

# adc_d[10] -> IO1_9N  (J10 第 19 针)
set_property PACKAGE_PIN U17 [get_ports {adc_d[10]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[10]}]

# adc_d[11] -> IO1_9P  (J10 第 20 针)   ← MSB 侧
set_property PACKAGE_PIN T16 [get_ports {adc_d[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {adc_d[11]}]

# adc_otr   -> IO1_10P (J10 第 22 针)
set_property PACKAGE_PIN V17 [get_ports adc_otr]
set_property IOSTANDARD LVCMOS33 [get_ports adc_otr]

# loop_en  -> IO1_11N (J10 第 23 针)   ★ 闭环使能（高有效）
#   XDC 里配 PULLDOWN → 上电默认【开环】（固定 20% 占空比）
#   要闭环时必须特意用杜邦线把这一针接到 3V3（第 39/40 针）✓ 安全设计
set_property PACKAGE_PIN T15 [get_ports loop_en]
set_property IOSTANDARD LVCMOS33 [get_ports loop_en]
set_property PULLDOWN true [get_ports loop_en]

# 备用池（未使用，留给 DAC / 故障来源区分）：
#   IO1_10N = V18 (第 21 针)   IO1_11P..IO1_17 = 第 24~36 针


# adc_inv_off -> IO1_10N (J10 第21针, V18)  ADC 数据取反禁能
#   悬空(内部下拉)=取反 ✓ / 接 3V3=不取反
set_property PACKAGE_PIN V18 [get_ports adc_inv_off]
set_property IOSTANDARD LVCMOS33 [get_ports adc_inv_off]
set_property PULLDOWN true [get_ports adc_inv_off]
