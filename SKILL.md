---
name: stm32cubemx-cmake
description: Configure STM32F405 and STM32F103C8T6 MCUs through STM32CubeMX IOC files and its headless CLI, then generate and build official CMake projects. 自动用于根据原理图或接线配置 STM32 引脚、时钟、ADC、DMA、USB、UART 等外设，创建或修改 .ioc，并生成 CMake 工程的请求。
---

# STM32CubeMX configuration and CMake

通过 `.ioc` 和本机 CubeMX CLI 配置单片机，默认生成官方 CMake 工程。使用非图形接口完成操作，保持 `.ioc` 可由 CubeMX 打开和再次生成。用户当次指定的工具链、目录布局和范围优先。

## Determine the target

先检查仓库说明、已有 `.ioc` 和代码。核对芯片完整型号、封装、晶振、电压、接线、调试接口及目标 USB 类。网络名与 ADC/串口实例分别核对。只对无法从材料确定、且会影响功能的缺项询问用户，其余工作继续推进。

根据已有代码重建时，将实际初始化和调用方式与 `.ioc` 对照，记录源码手动改动和缺失参数。匹配应用的轮询、连续转换、DMA、中断及 EOC 语义，依据代码和接线选择上下拉。核对 USER CODE 标记配对和重复结束标记，迁移后先编译，再验证再次生成。

用户要求验证技能生成能力时，先让 CubeMX 生成纯框架，核对引脚、时钟、外设依赖及 CMake，并单独编译，再接入应用代码。保留框架检查结果并说明有意采用的配置差异。交付时明确 CubeMX 生成部分、自行实现部分和沿用或迁移的参考代码及参数。

配置 F405 时读取 [family-profiles.md](references/family-profiles.md) 的 F405 段，配置 F103C8T6 时读取 F103 段。模板和示例中的 8 MHz 晶振与引脚只代表示例条件，根据板上实际接线调整。

遵循用户的版本目录约定。已有已交付或已烧录工程需要保留时，先保留完整源码及固件，再在下一代目录开发。每个版本直接放置完整可编译工程，说明用途、改动、产物位置及验证状态。

## Discover tools and configuration data

定位本机 CubeMX 及其 Java、对应 STM32Cube 固件包、CMake、Ninja 和 ARM GCC。优先使用显式路径或环境变量 `CUBEMX_PATH`、`CUBEMX_JAVA`，其次检查 PATH、安装登记和常见目录。运行日志和保存后的 `.ioc` 用于核实实际版本。遵循现有工程的版本选择，记录迁移差异。

从本机 CubeMX `db/mcu`、`db/mcu/IP` 和配置映射查询当前版本支持的引脚信号、外设模式、参数名及合法值。需要时查 ST 官方数据手册和参考手册。

## Edit IOC

使用本机 CubeMX 为准确型号创建基线，或在现有 `.ioc` 上修改。按字段依赖维护 `Mcu.IP*`、`Mcu.IPNb`、`Mcu.Pin*`、`Mcu.PinsNb`、`IPParameters`、`SH.*`、ADC Rank、DMA 请求及 NVIC。保留用户已有中间件、代码生成选项和代码。

逐项核对 GPIO 模式、上下拉和标签，外部上拉且按下接地的按键通常采用 Input、No pull、低电平有效。核对晶振模式、总线/ADC/USB 时钟、供电允许频率、DMA 映射和中断顺序，使用匹配家族的 HAL 字段。将选定的主频、采样时间等可逆默认值记录在交付说明中。

USB 按板上接线和用户协议配置。保留需要的 SWD 引脚，检查 JTAG 引脚复用和 AFIO 重映射。生成后从实际宏和初始化语句核对引脚数量，避免数组或字符串拼接错误。

已有 USB 应用需要检查自定义类注册、设备/配置/HID 描述符、接口数量、VID/PID、端点与 FIFO，以及 CMake 中的自定义源码。自定义复合设备可能只在 `.ioc` 中表现为 CDC。将可表达的配置写入 `.ioc`，其余生成区扩展通过可重复执行的生成后步骤恢复，并实际验证再次生成和编译。自定义源码优先加入用户维护的顶层 CMake。

## Generate and build

可用 [scripts/cubemx_generate.py](scripts/cubemx_generate.py) 调用官方生成器。脚本依赖 Python 3.10+ 标准库。对指定 `.ioc` 所在工程执行生成，修改文件前按工程上下文完成备份或版本保留。

```text
python scripts/cubemx_generate.py --ioc /absolute/project/Board.ioc --cubemx /absolute/install/STM32CubeMX.exe --build
```

Windows `.exe` 默认使用安装目录中的 `jre/bin/java.exe` 启动 `-jar ... -q`。Linux/macOS 使用原生可执行文件，通过 `--cubemx` 指定，JAR 可配合 `--java`。环境变量仅用于本机发现，发布内容使用通用路径。

脚本把加载 `.ioc`、选择 CMake、按绝对路径保存配置和 `project generate` 各写一行，以 `.ioc` 所在目录作为工作目录和生成位置，保存本地日志、检查生成状态和必要文件。需要自定义流程时直接使用同样的官方 CLI。`project generate` 生成完整工程。

现有项目编译使用其正常入口或预设。脚本 `--build` 使用标准 `Debug` 预设，可通过 `--preset` 调整。构建错误需定位并修复，缺少依赖时明确报告。

## Verify and deliver

- 核对 GPIO、时钟、ADC Rank、DMA、NVIC、USB 描述符和初始化顺序。DMA 控制器初始化应在依赖它的外设初始化之前完成。
- 检查日志中的错误和导入提示。CubeMX 有时会输出 `OptionalMessage_ERROR` 后继续生成，需逐条对照最终 `.ioc` 和源码判断，不能只看进程退出码。
- 新建或显著修改配置时，再次加载和生成，确认参数及用户代码保留。用户要求一致性时对相关源码和 CMake 文件做内容对比，记录版本和元数据差异。
- 交付完整 `.ioc`、CMake 工程、关键参数、引脚表、工具/固件包版本、产物位置及验证状态。
- 单纯配置请求交付初始化工程，明确 ADC 启动、校准、消抖和通信业务的完成状态。要求运行功能时完成相应应用代码。编译、实物烧录、USB 枚举和信号采集按实际结果分别报告。

准备公开分享时，只打包技能、通用说明、脚本及脱敏示例。检查用户名、本机绝对路径、设备标识、原理图、私人代码、凭证、日志和 Git 历史。发布包按显式清单构建，并对解压内容再检查。
