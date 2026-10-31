#===========================================================================
# build_ila.tcl —— 在现有工程里加入 ILA_0（6 探针）并重新综合实现出比特流
#----------------------------------------------------------------------------
# 目的：片内测量 pwm_h / pwm_l 的死区（200 MHz 采样 = 5 ns 分辨率）
# 探针：probe0 pwm_h(1) probe1 pwm_l(1) probe2 pwm_tick(1)
#       probe3 fault_i(1) probe4 SD(1) probe5 duty_used(11)
# 深度：2048（200 MHz 下 = 10.24 µs，覆盖 2 个开关周期）
#===========================================================================

set root "E:/D/PROJECTS/fpga/vivado_proj"
set prj  "$root/dpwm_top"

puts "===== 打开工程 ====="
open_project "$prj/dpwm_top.xpr"

puts "===== 添加 ILA IP（6 探针，若已存在则跳过）====="
# 注意：Vivado 的 ILA IP **改探针数必须删掉 IP 重建**，set_property 对已生成的 IP 不生效。
#       所以这里保持 6 探针不变；换观测对象就改 dpwm_top.v 里的探针连接（宽度匹配即可）。
if {[llength [get_ips -quiet ila_0]] == 0} {
    create_ip -name ila -vendor xilinx.com -library ip -module_name ila_0
    set_property -dict [list \
        CONFIG.C_NUM_OF_PROBES {6} \
        CONFIG.C_PROBE0_WIDTH {1} \
        CONFIG.C_PROBE1_WIDTH {1} \
        CONFIG.C_PROBE2_WIDTH {1} \
        CONFIG.C_PROBE3_WIDTH {1} \
        CONFIG.C_PROBE4_WIDTH {1} \
        CONFIG.C_PROBE5_WIDTH {11} \
        CONFIG.C_DATA_DEPTH {2048} \
        CONFIG.C_INPUT_PIPE_STAGES {1} \
    ] [get_ips ila_0]
    generate_target all [get_ips ila_0]
    puts "ila_0 已创建（6 探针）"
} else {
    puts "ila_0 已存在（保持 6 探针）"
}

puts "===== 确保 adc_if.v / comp_2p2z.v 在工程里 ====="
foreach f {adc_if comp_2p2z} {
    if {[llength [get_files -quiet $f.v]] == 0} {
        add_files -norecurse "$root/src/$f.v"
        puts "$f.v 已加入工程"
    } else {
        puts "$f.v 已在工程里"
    }
}

puts "===== 重新综合 ====="
reset_run synth_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
puts "SYNTH: [get_property PROGRESS [get_runs synth_1]] / [get_property STATUS [get_runs synth_1]]"

puts "===== 重新实现 + 比特流 ====="
reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
puts "IMPL: [get_property PROGRESS [get_runs impl_1]] / [get_property STATUS [get_runs impl_1]]"

if {[catch {
    open_run impl_1
    puts "WNS(setup) = [get_property SLACK [get_timing_paths -max_paths 1 -setup]] ns"
} err]} { puts "时序读取: $err" }

puts "BITSTREAM = [glob -nocomplain $prj/dpwm_top.runs/impl_1/*.bit]"
puts "LTX       = [glob -nocomplain $prj/dpwm_top.runs/impl_1/*.ltx]"
puts "===== DONE ====="
