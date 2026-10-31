# Vivado IP 配置（clk_wiz_0 / ila_0）

本目录是上板工程用到的两个 Vivado IP Catalog 核的原始配置文件，以及重建 ILA 的脚本。**这两个核是 `rtl/dpwm_top.v` 直接实例化的**（`u_clk_wiz` 提供 200 MHz 系统时钟，`u_ila` 是调试用逻辑分析仪），所以缺了它们工程无法综合。

| 文件 | 说明 |
| --- | --- |
| `clk_wiz_0.xci` | Clocking Wizard 6.0（rev 11）：输入板载 50 MHz → 输出 **200 MHz** + `locked`，即 DPWM 的 5 ns 时间分辨率来源 |
| `ila_0.xci` | ILA 6.2（rev 12）：**6 探针 / 深度 2048**（200 MHz 下 10.24 µs 窗口，覆盖 2 个开关周期） |
| `build_ila.tcl` | 在已有工程里加入 `ila_0` 并重跑综合/实现/比特流的脚本（幂等，已存在则跳过） |

器件为 **`xc7z020`（Zynq-7020，AX7020 开发板）**，配置文件由 **Vivado 2022.2** 生成。

## ILA 探针分配

| 探针 | 信号 | 宽度 |
| --- | --- | --- |
| probe0 | `pwm_h` | 1 |
| probe1 | `pwm_l` | 1 |
| probe2 | `pwm_tick` | 1 |
| probe3 | `fault_i` | 1 |
| probe4 | `SD` | 1 |
| probe5 | `duty_used` | 11 |

> 改探针数必须删除 IP 重建（`set_property` 对已生成的 ILA 不生效），所以脚本固定保持 6 探针；要换观测对象就改 `rtl/dpwm_top.v` 里的探针连接（宽度匹配即可）。

## 怎么用

1. **自己建工程**（仓库不提供 `.xpr`，因为它含本机绝对路径）：
   - 新建 RTL 工程，器件选 `xc7z020clg400-2`（AX7020）；
   - 加入 `../rtl/` 下四个 `.v` 与 `../xdc/dpwm_top.xdc`；
   - 把本目录两个 `.xci` 用 *Add Sources → Add Existing IP* 加进工程（或 `add_files clk_wiz_0.xci ila_0.xci`）。
2. **或者只重建 ILA**（已有工程，只想加调试核）：
   ```
   vivado -mode batch -source build_ila.tcl -tclargs D:/work/vivado_proj
   ```
   脚本按「命令行参数 → 环境变量 `FPGA_PRJ_ROOT` → 当前目录下 `vivado_proj/`」的顺序找工程根目录，其下应存在 `dpwm_top/dpwm_top.xpr` 与 `src/{adc_if,comp_2p2z}.v`。
3. 不用 ILA 调试时，注释掉 `rtl/dpwm_top.v` 中的 `u_ila` 实例即可，其余逻辑不受影响。

## 验证情况（如实说明）

- 两个 `.xci` 已核对为合法 Vivado 2022.2 IP 配置文件（`schema: xilinx.com:schema:json_instance:1.0`，`component_reference` 分别为 `clk_wiz:6.0`／`ila:6.2`，`DEVICE = xc7z020`）。
- `rtl/` 下四个模块已用 `xvlog` 独立编译通过（exit 0），`xelab` 只报这两个 IP 未定义——正因为当时仓库里没有它们。现在补齐后，**在完整 Vivado 工程里尚未做一次工程级综合**（仓库不含 `.xpr`），如有综合告警请以实际工程为准。
