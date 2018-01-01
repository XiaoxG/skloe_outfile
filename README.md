# SKLOE OUT FILE READER
## Developed by Xiaoxian Guo and Zhichao Fang

### 简介

基于python3.6 (Anaconda) 环境开发，主要针对FDAS处理后的数据，进行进一步后处理，实现数据读入，数据处理，数据输出。

FDAS主要对单个工况数据进行处理，我们希望基于python开发进一步的后处理工具，提高工作效率，并提供python接口，可以实现更多的实时功能。

主要应用场景：

- 针对不同工况，同一通道的数据横向对比分析
- 标准化的批量报表自动生成
- 标准化的数据后处理，针对刚度试验，衰减试验
- 便捷的自定义数据处理
- 应用于自动校波、校风

...


目前程序托管于GitHub，主页为：https://github.com/XiaoxG/skloe_outfile

HELP：https://nbviewer.jupyter.org/github/XiaoxG/skloe_outfile/blob/master/readme.ipynb

目前拥有以下功能：

1. *.out 文件读入功能
2. 打印文件基本信息到显示屏，txt文本，Excel文本 （包括：段数，通道数，采样频率，采样时间，前标定段信息，各个通道单位，通道名，系数，每段数据的采样点数，起止时间等）
3. 打印基本统计信息到显示屏，txt文本，Excel文本 （包括：最大值，最小值，方差，均值，点数等）
4. 输出数据至*.mat文件或*.dat文件
5. 通道单位修复 （原out文件通道单位不能超过4个字符）
6. 实型值转换
7. 简单的数据时域统计分析（基于Pandas）

正在开发功能：

- 波浪数据频、时域分析（基于WAFO）
- 校波文件读入与波浪自动对齐相位
- 静刚度试验模块
- 合并运动文件

待开发功能：

- 运动数据读入与自动对齐相位
- *.out 文件写入（或使用通用二进制文件）
- 标准化报表自动生成 （pdf,latex）
- 标准化波浪数据频域分析
- 标准化衰减试验模块

系统要求：

- Python version 3.6.3 |Anaconda custom (64-bit)|
- Pandas version 0.20.3
- Matplotlib version 2.1.0
- Scipy version 0.19.1

强烈推荐使用Anaconda 构建Python科学计算环境

Anaconda: https://www.anaconda.com

读入数据后，数据类型为pandas.DataFrame，基于pandas库的各种函数均可调用，请发挥你的想象力。

Pandas documents: https://pandas.pydata.org

后续版本将基于WAFO开发统计处理模块，包括时域分析，频谱转换，极值预报，统计模型检验，疲劳分析等。

强烈推荐WAFO模块（Matlab, Python）: http://www.maths.lth.se/matstat/wafo/

更多功能会陆续推出，欢迎大家在Github平台参与代码开发

如有任何问题请联系：xiaoxguo@sjtu.edu.cn
