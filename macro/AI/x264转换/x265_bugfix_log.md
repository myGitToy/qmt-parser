# x265转换器错误修复日志

## v2.1 修复 - 2025年7月3日

### 🐛 问题描述
**错误类型**: Python闭包（Closure）错误  
**错误信息**: `NameError: free variable 'e' referenced before assignment in enclosing scope`

### 🔍 问题原因
在异常处理的`except`块中，使用了`self.root.after()`调用lambda函数，而lambda函数中直接引用了异常变量`e`。由于Python的闭包机制，当lambda函数在后续执行时，变量`e`可能已经超出作用域或被修改。

### 🔧 修复方案
将需要在lambda中使用的变量提前赋值给局部变量，避免闭包引用问题：

**修复前:**
```python
except Exception as e:
    self.root.after(1, lambda: self.log(f"💥 转换过程中出错: {str(e)}"))
    self.root.after(1, lambda: messagebox.showerror("错误", f"转换过程中出错: {str(e)}"))
```

**修复后:**
```python
except Exception as e:
    error_msg = str(e)  # 提前获取错误信息
    self.root.after(1, lambda: self.log(f"💥 转换过程中出错: {error_msg}"))
    self.root.after(1, lambda: messagebox.showerror("错误", f"转换过程中出错: {error_msg}"))
```

### ✅ 修复内容
1. **异常处理区域**: 修复`convert_thread`方法中的异常处理lambda函数
2. **转换结果处理**: 修复转换成功和失败时的输出信息lambda函数
3. **变量捕获**: 使用局部变量避免闭包引用问题

### 🧪 修复验证
- ✅ Python语法检查通过 (`python -m py_compile demo_x265.py`)
- ✅ 代码逻辑正确，避免了运行时错误
- ✅ 保持原有功能不变

### 📚 技术说明
**Python闭包注意事项:**
- Lambda函数中引用的外部变量在定义时被捕获
- 如果变量在lambda执行时已经超出作用域，会导致NameError
- 解决方案：使用默认参数或提前赋值给局部变量

**最佳实践:**
```python
# 方案1: 使用默认参数
self.root.after(1, lambda msg=error_msg: self.log(msg))

# 方案2: 提前赋值（本次采用）
error_msg = str(e)
self.root.after(1, lambda: self.log(error_msg))
```

### 🎯 影响范围
- **影响功能**: 错误处理和转换结果显示
- **修复效果**: 消除运行时异常，提升程序稳定性
- **用户体验**: 无变化，错误信息正常显示

---

## v2.1.1 修复 - 2025年7月3日

### 🐛 问题描述
**错误类型**: Windows系统编码错误  
**错误信息**: `'gbk' codec can't decode byte 0xaf in position 58: illegal multibyte sequence`

### 🔍 问题原因
在Windows系统上，Python的subprocess模块默认使用系统编码（通常是GBK），而FFmpeg输出包含UTF-8编码的字符（如版权符号©等），导致编码解析失败。

### 🔧 修复方案
为所有subprocess调用明确指定UTF-8编码，并设置错误处理策略：

**修复前:**
```python
subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
```

**修复后:**
```python
subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               check=True, encoding='utf-8', errors='replace')
```

### ✅ 修复内容
1. **FFmpeg版本检查**: 添加UTF-8编码支持
2. **GPU编码器检查**: 修复编码器列表解析
3. **视频信息获取**: 修复ffprobe输出解析
4. **转换进程**: 修复FFmpeg输出流编码
5. **错误处理**: 使用`errors='replace'`避免解码失败

### 🧪 修复验证
- ✅ Windows 11系统测试通过
- ✅ FFmpeg 7.1.1版本兼容
- ✅ 含有特殊字符的输出正常解析

### 📚 技术说明
**编码问题原因:**
- Windows系统默认使用GBK/CP936编码
- FFmpeg输出使用UTF-8编码，包含©、™等符号
- Python subprocess默认使用系统编码，导致解析失败

**修复策略:**
```python
# 统一使用UTF-8编码
encoding='utf-8'
# 遇到无法解码字符时替换为?
errors='replace'
```

### 🎯 影响范围
- **影响功能**: 所有FFmpeg相关调用
- **修复效果**: 完全解决Windows编码问题
- **兼容性**: 保持Linux/macOS系统兼容性

---
**修复人员**: GitHub Copilot  
**修复时间**: 2025年7月3日  
**版本号**: v2.1.1
