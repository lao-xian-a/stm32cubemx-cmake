# Family profiles

## STM32F405

适配 F405 时以完整料号、Flash 容量和封装为准。示例使用 STM32F405RGT6 / LQFP64，CubeMX 标识为 `STM32F405RGTx`，1 MiB Flash、128 KiB 常规 SRAM 和 64 KiB CCM。其他 F405 封装及容量需重新查询本机数据库。

3.3 V、8 MHz HSE 晶振的示例时钟为 PLL M=8、N=336、P=2、Q=7，SYSCLK=168 MHz，APB1=42 MHz，APB2=84 MHz，USB=48 MHz。依供电和目标频率核对电压缩放及 Flash latency。

ADC1 的 PA0/PA1 对应 IN0/IN1。示例为 12 位、两通道扫描、连续转换、480-cycle sampling，APB2 / 4 得到 ADC 21 MHz。在 VDDA 2.4–3.6 V 条件下 ADC 最大时钟为 36 MHz，较低 VDDA 需要采用对应的更低限值。采样时间取决于源阻抗和目标速率。

ADC1 DMA 可用 DMA2 Stream0 Channel0，使用半字、内存递增和 circular。其他外设使用数据库中的 Stream/Channel 映射，并检查资源冲突。DMA 缓冲区放在 DMA 可访问的常规 SRAM，CCM RAM 无 DMA 访问能力。

USB FS 使用 USB_OTG_FS，PA11 DM / PA12 DP。VBUS sensing 是否开启取决于 PA9 与板上 VBUS 的实际连接。ADC 的 `DMAContinuousRequests`、Stream/Channel 和 OTG 配置属于 F4 的实现。

SWD 为 PA13 / PA14。需要 PB3/PB4 等 JTAG 相关引脚时选择 Serial Wire，并核对生成的初始化结果。GPIO 复用使用对应 AF 编号。

## STM32F103C8T6

CubeMX 可使用 `STM32F103C8Tx` 加载，保存时 `Mcu.Name` 可能显示共享数据库标识 `STM32F103C(8-B)Tx`，以 `Mcu.CPN=STM32F103C8T6` 和具体容量为准。LQFP48，64 KiB Flash、20 KiB SRAM，Cortex-M3。链接脚本按 C8 标称容量生成。

3.3 V、8 MHz HSE 晶振的示例使用 PLL x9，SYSCLK=72 MHz，APB1=36 MHz，APB2=72 MHz。USB 分频 /1.5 得到 48 MHz。ADC 最大时钟为 14 MHz，PCLK2 /6 得到 12 MHz。默认 /2 会产生 36 MHz，需要显式核对并修正。

ADC1 PA0/PA1 为 IN0/IN1。示例为两通道扫描、连续转换、239.5-cycle sampling。F1 的扫描参数使用 `ADC_SCAN_ENABLE`。DMA 使用 DMA1 Channel1、半字、内存递增、circular。F1 的 DMA 以 Channel 分配，ADC 的连续 DMA 机制和 HAL 字段遵循 F1。应用启动 ADC 之前根据 HAL 要求执行 `HAL_ADCEx_Calibration_Start` 并检查返回值。

USB 使用 USB Device 外设与 USB_DEVICE CDC 中间件，PA11 / PA12。按硬件检查 D+ 上拉及需要的连接控制，USB/CAN 的共享资源和中断也需要核对。没有 F405 的 OTG VBUS-sensing 配置。晶振和 PLL 必须满足 USB 时钟要求。

SWD 为 PA13 / PA14。使用 PA15、PB3、PB4 时，根据需求关闭 JTAG 并保留 SWD，生成代码通常包含 AFIO SWJ remap。UART、SPI、I2C、TIM 的引脚重映射通过 AFIO 配置，并检查实际 remap 选项。GPIO 输入上拉/下拉按 F1 HAL 的模式及 Pull 配置核对。

## Example scope and verification

`examples/f405_demo.ioc` 和 `examples/f103c8_demo.ioc` 使用 8 MHz 晶振、PA0/PA1 两路 ADC 扫描与循环 DMA、PB0 外部上拉低有效输入、PA11/PA12 USB CDC、PA13/PA14 SWD。它们是通用初始化示例，根据实际原理图修改后使用。

## Primary references

- [STM32F405/407 datasheet](https://www.st.com/resource/en/datasheet/stm32f405rg.pdf)
- [STM32F103x8/xB datasheet](https://www.st.com/resource/en/datasheet/stm32f103c8.pdf)
- [STM32CubeMX CLI](https://dev.st.com/stm32cube-docs/stm32cubemx/6.18.0/en/docs/markup/CubeMX_CLI.html)
