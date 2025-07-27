import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path

class X264ToX265Converter:
    def __init__(self, root):
        self.root = root
        self.root.title("x264 转 x265 转换器")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # 存储当前进程引用
        self.current_process = None
        
        # 转换开始时间
        self.conversion_start_time = None
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.input_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出文件选择
        ttk.Label(main_frame, text="输出文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # 质量设置
        ttk.Label(main_frame, text="质量 (CRF):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.IntVar(value=28)
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=2, column=1, sticky=tk.EW, pady=5)
        ttk.Scale(quality_frame, from_=0, to=51, orient=tk.HORIZONTAL, 
                  variable=self.quality_var, command=self.update_quality_label).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.quality_label = ttk.Label(quality_frame, text="28")
        self.quality_label.pack(side=tk.RIGHT, padx=5)
        ttk.Label(main_frame, text="(0-51, 值越小质量越高)").grid(row=2, column=2, sticky=tk.W, pady=5)

        # GPU加速选项
        self.use_gpu = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="使用GPU加速", variable=self.use_gpu).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.gpu_type = tk.StringVar(value="nvidia")
        gpu_frame = ttk.Frame(main_frame)
        gpu_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(gpu_frame, text="GPU类型:").pack(side=tk.LEFT)
        ttk.Combobox(gpu_frame, textvariable=self.gpu_type, values=["nvidia", "amd", "intel"]).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        ttk.Label(main_frame, text="进度:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.grid(row=4, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        # 输出日志
        ttk.Label(main_frame, text="日志:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.log_text = tk.Text(main_frame, height=10, width=50, wrap=tk.WORD)
        self.log_text.grid(row=5, column=1, columnspan=2, sticky=tk.NSEW, pady=5)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=5, column=3, sticky=tk.NS)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 转换按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=1, pady=10)
        
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="取消转换", command=self.cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # 设置行列权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 检查FFmpeg是否安装
        self.check_ffmpeg()
        
        # 检查GPU编码器
        if self.convert_button['state'] != tk.DISABLED:
            self.check_gpu_encoders()
    
    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                         check=True, encoding='utf-8', errors='replace')
            self.log("✅ FFmpeg 已安装，可以开始转换")
        except (subprocess.SubprocessError, FileNotFoundError):
            self.log("❌ 错误: FFmpeg 未安装或不在系统路径中。请先安装 FFmpeg。")
            self.convert_button.configure(state=tk.DISABLED)
            messagebox.showerror("错误", "FFmpeg 未安装或不在系统路径中。请先安装 FFmpeg。")
    
    def check_gpu_encoders(self):
        """检查可用的GPU编码器"""
        encoders = {"nvidia": "hevc_nvenc", "amd": "hevc_amf", "intel": "hevc_qsv"}
        available_encoders = []
        
        for gpu_type, encoder in encoders.items():
            try:
                result = subprocess.run([
                    "ffmpeg", "-hide_banner", "-encoders"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, 
                timeout=5, encoding='utf-8', errors='replace')
                
                if encoder in result.stdout:
                    available_encoders.append(gpu_type)
                    self.log(f"✅ {gpu_type.upper()} 编码器 ({encoder}) 可用")
                else:
                    self.log(f"❌ {gpu_type.upper()} 编码器 ({encoder}) 不可用")
            except Exception as e:
                self.log(f"❌ 检查 {gpu_type.upper()} 编码器时出错: {e}")
        
        if available_encoders:
            self.log(f"📋 可用的GPU编码器: {', '.join(available_encoders)}")
        else:
            self.log("⚠️ 未检测到可用的GPU编码器，将使用CPU编码")
            self.use_gpu.set(False)
        
        return available_encoders
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="选择输入文件",
            filetypes=[("视频文件", "*.mkv *.mp4 *.avi *.mov *.wmv"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_var.set(filename)
            # 自动生成输出文件名
            input_path = Path(filename)
            output_file = str(input_path.with_name(f"{input_path.stem}_x265{input_path.suffix}"))
            self.output_var.set(output_file)
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="选择输出文件",
            defaultextension=".mkv",
            filetypes=[("视频文件", "*.mkv *.mp4 *.avi *.mov"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_var.set(filename)
    
    def update_quality_label(self, event=None):
        self.quality_label.configure(text=str(self.quality_var.get()))
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_conversion(self):
        input_file = self.input_var.get()
        output_file = self.output_var.get()
        quality = self.quality_var.get()
        
        if not input_file:
            messagebox.showerror("错误", "请选择输入文件")
            return
        
        if not output_file:
            messagebox.showerror("错误", "请选择输出文件")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("错误", f"输入文件不存在: {input_file}")
            return
        
        self.convert_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.progress.start(10)
        
        # 在单独的线程中运行转换以避免冻结UI
        threading.Thread(target=self.convert_thread, args=(input_file, output_file, quality), daemon=True).start()
    
    def cancel_conversion(self):
        """取消当前转换"""
        if self.current_process and self.current_process.poll() is None:
            try:
                self.log("🛑 正在取消转换...")
                self.current_process.terminate()
                
                # 等待进程终止
                import time
                for i in range(10):  # 等待最多10秒
                    if self.current_process.poll() is not None:
                        break
                    time.sleep(1)
                
                # 如果进程仍未终止，强制杀死
                if self.current_process.poll() is None:
                    self.current_process.kill()
                    self.log("💀 强制终止转换进程")
                else:
                    self.log("✅ 转换已取消")
                
                self.progress.stop()
                self.convert_button.configure(state=tk.NORMAL)
                self.cancel_button.configure(state=tk.DISABLED)
                self.root.title("x264 转 x265 转换器")
                
            except Exception as e:
                self.log(f"❌ 取消转换时出错: {e}")
                messagebox.showerror("错误", f"取消转换时出错: {e}")
    
    def convert_thread(self, input_file, output_file, quality):
        try:
            import time
            self.conversion_start_time = time.time()  # 记录开始时间
            
            self.log(f"🚀 开始转换: {os.path.basename(input_file)}")
            self.log(f"📁 输出文件: {os.path.basename(output_file)}")
            self.log(f"⚙️ 使用参数: CRF={quality}, GPU加速={self.use_gpu.get()}")
            self.log(f"⏰ 转换开始时间: {time.strftime('%H:%M:%S', time.localtime(self.conversion_start_time))}")
            
            # 构建FFmpeg命令
            if self.use_gpu.get():
                gpu_type = self.gpu_type.get().lower()
                if gpu_type == "nvidia":
                    encoder = "hevc_nvenc"
                    quality_param = ["-cq", str(quality)]
                    preset = "p4"
                elif gpu_type == "amd":
                    encoder = "hevc_amf"
                    quality_param = ["-quality", "quality", "-qp_i", str(quality), "-qp_p", str(quality)]
                    preset = "medium"
                elif gpu_type == "intel":
                    encoder = "hevc_qsv"
                    quality_param = ["-global_quality", str(quality)]
                    preset = "medium"
                else:
                    encoder = "libx265"
                    quality_param = ["-crf", str(quality)]
                    preset = "medium"
                    
                self.log(f"🎮 使用GPU编码器: {encoder}")
                command = [
                    "ffmpeg", "-y",  # 添加 -y 参数自动覆盖输出文件
                    "-i", input_file,
                    "-c:v", encoder
                ] + quality_param + [
                    "-preset", preset,
                    "-c:a", "copy",
                    "-c:s", "copy",
                    "-tag:v", "hvc1",
                    output_file
                ]
            else:
                command = [
                    "ffmpeg", "-y",  # 添加 -y 参数自动覆盖输出文件
                    "-i", input_file,
                    "-c:v", "libx265",
                    "-crf", str(quality),
                    "-preset", "medium",
                    "-c:a", "copy",
                    "-c:s", "copy",
                    "-tag:v", "hvc1",
                    output_file
                ]
            
            # 记录完整命令（简化显示）
            cmd_display = ' '.join([
                "ffmpeg", "-y", "-i", f'"{os.path.basename(input_file)}"',
                "-c:v", command[command.index("-c:v") + 1],
                "...", f'"{os.path.basename(output_file)}"'
            ])
            self.log(f"🔧 执行命令: {cmd_display}")
            
            # 获取总帧数
            total_frames = self.get_total_frames(input_file)
            
            if total_frames:
                self.root.after(1, lambda: self.progress.config(mode='determinate', maximum=total_frames))
                self.log(f"📊 视频总帧数: {total_frames:,}")
            else:
                self.root.after(1, lambda: self.progress.config(mode='indeterminate'))
                self.root.after(1, lambda: self.progress.start(10))
                self.log("📊 无法获取总帧数，使用未知进度模式")
            
            # 启动FFmpeg进程
            self.log("🎬 启动FFmpeg进程...")
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
                universal_newlines=True,
                encoding='utf-8',  # 明确指定UTF-8编码
                errors='replace',  # 遇到编码错误时替换为?字符
                bufsize=1
            )
            
            self.log("✅ FFmpeg进程已启动，开始监控输出...")
            
            import re
            frame_re = re.compile(r"frame= *([0-9]+)")
            speed_re = re.compile(r"speed= *([0-9.]+)x")
            time_re = re.compile(r"time=([0-9:\.]+)")
            
            line_count = 0
            last_frame = 0
            last_log_time = 0
            
            # 读取输出
            for line in self.current_process.stdout:
                line_count += 1
                line = line.strip()
                
                if line:
                    current_time = time.time()
                    
                    # 检查是否包含重要信息
                    is_important = (
                        "error" in line.lower() or 
                        "warning" in line.lower() or
                        "failed" in line.lower() or
                        line.startswith("Input #") or
                        line.startswith("Output #") or
                        "Stream mapping:" in line
                    )
                    
                    # 每30秒或重要信息时显示详细输出
                    if current_time - last_log_time > 30 or is_important:
                        last_log_time = current_time
                        self.root.after(1, lambda l=line: self.log(l))
                    
                    # 解析进度信息
                    if total_frames:
                        match = frame_re.search(line)
                        if match:
                            frame = int(match.group(1))
                            if frame > last_frame:  # 只在帧数增加时更新
                                last_frame = frame
                                percent = min(100, int(frame / total_frames * 100))
                                self.root.after(1, self.set_progress, frame, percent)
                                
                                # 每500帧显示一次详细进度
                                if frame % 500 == 0:
                                    speed_match = speed_re.search(line)
                                    if speed_match:
                                        speed = float(speed_match.group(1))
                                        eta_seconds = (total_frames - frame) / (speed * 25) if speed > 0 else 0
                                        eta_minutes = int(eta_seconds / 60)
                                        self.root.after(1, lambda f=frame, s=speed, e=eta_minutes: 
                                                       self.log(f"⚡ 进度: {f:,}/{total_frames:,} 帧 ({percent}%), 速度: {s:.1f}x, 预计剩余: {e}分钟"))
            
            # 等待进程完成
            self.current_process.wait()
            
            # 恢复界面状态
            self.root.after(1, lambda: self.root.title("x264 转 x265 转换器"))
            if total_frames:
                self.root.after(1, self.set_progress, total_frames, 100)
            
            # 检查转换结果
            if self.current_process.returncode == 0:
                # 计算总耗时
                end_time = time.time()
                total_time = end_time - self.conversion_start_time
                hours = int(total_time // 3600)
                minutes = int((total_time % 3600) // 60)
                seconds = int(total_time % 60)
                
                if hours > 0:
                    time_str = f"{hours}小时{minutes}分钟{seconds}秒"
                elif minutes > 0:
                    time_str = f"{minutes}分钟{seconds}秒"
                else:
                    time_str = f"{seconds}秒"
                
                file_size = os.path.getsize(output_file) / (1024*1024*1024)  # GB
                output_name = os.path.basename(output_file)  # 提前获取文件名
                self.root.after(1, lambda: self.log(f"🎉 转换成功: {output_name} ({file_size:.1f}GB)"))
                self.root.after(1, lambda: self.log(f"⏱️ 总耗时: {time_str}"))
                self.root.after(1, lambda: messagebox.showinfo("成功", f"转换已完成!\n总耗时: {time_str}"))
            else:
                return_code = self.current_process.returncode  # 提前获取返回码
                self.root.after(1, lambda: self.log(f"❌ 转换失败: 返回代码 {return_code}"))
                self.root.after(1, lambda: messagebox.showerror("错误", "转换失败!"))
                
        except Exception as e:
            error_msg = str(e)  # 提前获取错误信息
            self.root.after(1, lambda: self.log(f"💥 转换过程中出错: {error_msg}"))
            self.root.after(1, lambda: messagebox.showerror("错误", f"转换过程中出错: {error_msg}"))
        finally:
            # 恢复界面状态
            self.root.after(1, lambda: self.progress.stop())
            self.root.after(1, lambda: self.convert_button.configure(state=tk.NORMAL))
            self.root.after(1, lambda: self.cancel_button.configure(state=tk.DISABLED))
            self.current_process = None

    def set_progress(self, frame, percent):
        self.progress['value'] = frame
        self.root.title(f"x264 转 x265 转换器 - 进度: {percent}%")

    def get_total_frames(self, input_file):
        """通过ffprobe获取视频总帧数"""
        try:
            self.log("🔍 正在获取视频信息...")
            
            # 首先尝试快速方法
            result = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=nb_frames", "-of", "default=nokey=1:noprint_wrappers=1", input_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, 
            timeout=15, encoding='utf-8', errors='replace')
            
            frames = result.stdout.strip()
            if frames.isdigit() and int(frames) > 0:
                return int(frames)
            
            # 如果快速方法失败，尝试估算
            self.log("⚠️ 快速获取帧数失败，尝试估算...")
            return self.estimate_total_frames(input_file)
                
        except Exception as e:
            self.log(f"❌ 获取视频信息失败: {e}")
            return None
    
    def estimate_total_frames(self, input_file):
        """通过时长和帧率估算总帧数"""
        try:
            # 获取视频时长和帧率
            result = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=duration,r_frame_rate", 
                "-of", "default=noprint_wrappers=1:nokey=1", input_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, 
            timeout=10, encoding='utf-8', errors='replace')
            
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                duration = float(lines[0])
                fps_str = lines[1]
                
                if '/' in fps_str:
                    num, den = map(int, fps_str.split('/'))
                    fps = num / den
                else:
                    fps = float(fps_str)
                
                estimated_frames = int(duration * fps)
                self.log(f"📊 估算帧数: {estimated_frames:,} (时长: {duration:.1f}s, 帧率: {fps:.2f}fps)")
                return estimated_frames
            
        except Exception as e:
            self.log(f"❌ 估算帧数失败: {e}")
            
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = X264ToX265Converter(root)
    root.mainloop()