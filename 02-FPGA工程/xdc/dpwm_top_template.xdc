##====================================================================
## dpwm_top.xdc —— 引脚约束模板（B 线 2026-10-08 交付，配合 dpwm_top.v）
##--------------------------------------------------------------------
## 板卡：黑金 ALINX AX7020（xc7z020）
## 引脚资料来源：ALINX 官网 www.alinx.com → 资料下载 → AX7020
##   《AX7020 用户手册》+ 底板/核心板原理图 PDF
## 用法：A 线把所有【PIN_XX】换成实际引脚号后，改名为 dpwm_top.xdc 加入工程
##--------------------------------------------------------------------
## 三条铁律：
##   1) 时钟必须落在全局时钟 capable 引脚（板载 50 MHz 本来就在 CC 脚上，抄原理图即可）
##   2) 扩展口 IO 统一 LVCMOS33（AX7020 扩展 bank 3.3V 供电；以原理图 bank 电压为准）
##   3) 本文件故意不含 ADC_D[11:0]/OTR——等 AD9226 模块选型后再补（10/15 的活）
##====================================================================

## 1) 系统时钟：板载 50 MHz
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports clk_50m]
create_clock -period 20.000 -name sys_clk -waveform {0.000 10.000} [get_ports clk_50m]

## 2) 复位按键（按下=低；板上有外部上拉；引脚查原理图 KEY/RST 网络）
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports rst_btn_n]

## 3) 故障输入（H 区 ← 功率板 LM393 开集+3.3V 上拉）
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports FAULT_N]

## 4) PWM / SD / ADC_CLK（H 区 → 功率板）
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports pwm_h]
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports pwm_l]
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports SD]
set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports ADC_CLK]

## 5)【10/15 预留，先注释】ADC 数据总线 12 位 + OTR
# set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports {ADC_D[0]}]
# set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports {ADC_D[1]}]
# ...（ADC_D[2]..[11] 同格式）
# set_property -dict {PACKAGE_PIN 【PIN_XX】 IOSTANDARD LVCMOS33} [get_ports OTR]

## 6) 配置 bank（AX7020 常规设置；与 ALINX 官方例程 XDC 保持一致即可）
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
