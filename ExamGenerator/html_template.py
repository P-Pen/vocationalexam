"""
HTML模板生成器
根据题目类型生成对应的HTML文件
"""

import html


class HTMLTemplate:
    """HTML模板生成类"""
    
    def __init__(self):
        """初始化模板"""
        self.base_head = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="./static/bootstrap.min.css">
    <link rel="stylesheet" href="./static/toastify.css">
    <link rel="stylesheet" href="./static/viewer.min.css">
    <style>
		/* 禁止文本选择 */
		.disable-selected {{
			-webkit-user-select: none; /* Safari */
			-moz-user-select: none; /* Firefox */
			-ms-user-select: none; /* IE/Edge */
			user-select: none; /* 标准语法 */
		}}
		/* 全屏水印相关样式 */
		@layer utilities {{
            .watermark-container {{
                /* @apply fixed inset-0 pointer-events-none z-50 overflow-hidden; */
				position: fixed;
				top: 0;
				right: 0;
				bottom: 0;
				left: 0;
				pointer-events: none;
				z-index: 9999;
				overflow: hidden;
            }}
        }}
    </style>
  </head>
  <body>
"""
        
        self.base_foot = """	<!-- 水印容器 -->
    <div id="watermarkContainer" class="watermark-container"></div>
    <script src="./static/jquery.min.js"></script>
    <script src="./static/clipboard.min.js"></script>
    <script src="./static/bootstrap.min.js"></script>
    <script src="./static/toastify.js"></script>
    <script src="./static/viewer.min.js"></script>
    <script src="./static/jquery-viewer.min.js"></script>
    <script>
		var ShowWatermark = false; // 是否显示水印
		// 水印配置
        var watermarkConfig = null;
		// 创建水印
        function createWatermark() {{
            // 清空现有水印
            watermarkContainer.innerHTML = '';
            
            // 获取视口尺寸
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            // 计算水印数量
            const cols = Math.ceil(viewportWidth / watermarkConfig.spacing) + 1;
            const rows = Math.ceil(viewportHeight / watermarkConfig.spacing) + 1;
            
            // 创建水印元素
            for (let i = 0; i < rows; i++) {{
                for (let j = 0; j < cols; j++) {{
                    const watermark = document.createElement('div');
                    
                    // 设置水印样式
                    watermark.style.position = 'absolute';
                    watermark.style.left = `${{j * watermarkConfig.spacing}}px`;
                    watermark.style.top = `${{i * watermarkConfig.spacing}}px`;
                    watermark.style.transform = `rotate(${{watermarkConfig.rotation}}deg)`;
                    watermark.style.opacity = watermarkConfig.opacity;
                    watermark.style.fontSize = `${{watermarkConfig.fontSize}}px`;
                    watermark.style.color = watermarkConfig.color;
                    watermark.style.fontFamily = 'Arial, sans-serif';
                    watermark.style.whiteSpace = 'nowrap';
                    watermark.style.userSelect = 'none';
                    watermark.style.webkitUserSelect = 'none';
                    watermark.style.zIndex = '100';
                    
                    // 设置水印文本
                    watermark.textContent = watermarkConfig.text;
                    
                    // 添加到容器
                    watermarkContainer.appendChild(watermark);
                }}
            }}
        }}
        // 网页加载就绪
		$(document).ready(function() {{
			// AppBridge（不要动）
			CefSharp.BindObjectAsync("AppBridge");
			// 实现复制代码功能
			var clipboard = new ClipboardJS('.btncopy');
			clipboard.on('success', function(e) {{
				e.clearSelection();
				Toastify({{
					text: "复制成功"
				}}).showToast();
			}});
			{extra_script}
			// 接收来自宿主程序的水印
			window.watermark = function(text) {{
				if(ShowWatermark) {{
					watermarkConfig = {{
						text: text,
						rotation: -30,       // 旋转角度
						opacity: 0.05,        // 透明度
						fontSize: 20,        // 字体大小(px)
						spacing: 200,        // 水印间距(px)
						color: '#000000'     // 水印颜色
					}};
					createWatermark(); // 初始化水印
				}}
			}}
			// 禁止右键菜单
			document.addEventListener('contextmenu', function(e) {{
				e.preventDefault();
				return false;
			}});
			{extra_ready}
			// 图片放大
			var $image = $('#preview');
			$image.viewer({{
				inline: true,
				viewed: function() {{
					$image.viewer('zoomTo', 1);
				}}
			}});
			// Get the Viewer.js instance after initialized
			var viewer = $image.data('viewer');
			// View a list of images
			$('.zoom').viewer();
		}});
    </script>
  </body>
</html>
"""
    
    def generate_single_choice(self, number, question_text, options, code=''):
        """生成单选题HTML"""
        
        # 代码区域
        code_html = ''
        if code.strip():
            # 转义HTML特殊字符，但保留换行
            code_escaped = html.escape(code).replace('\n', '\n')
            code_html = f"""
		<!-- 代码区域（可选） -->
		<div class="row" style="margin-top: 10px;">
			<div class="col-md-12">
			
<pre id="code-1">
{code_escaped}</pre>

			</div>
		</div>
		<div class="row" style="padding-left: 10px;">
			<button type="button" class="btn btn-primary btn-sm btncopy" data-clipboard-target="#code-1">复制代码</button>
		</div>
		"""
        
        # 选项HTML
        options_html = ''
        for opt_key in ['A', 'B', 'C', 'D']:
            opt_value = options.get(opt_key, '')
            options_html += f"""		<!-- 选项{opt_key} -->
		<div class="row disable-selected"{' style="margin-top: 10px;"' if opt_key == 'A' else ''}>
			<div class="col-md-12{' ' if opt_key != 'A' else ''}">
				<div class="radio">
					<label>
						<input type="radio" name="options" id="option{opt_key}" value="{opt_key}">
						<span class="disable-selected" style="font-weight: bold; margin-right: 5px;">{opt_key}.</span>
						<!-- 选项{opt_key}内容 -->
						<span>{opt_value}</span>
					</label>
				</div>
			</div>
		</div>
"""
        
        body = f"""	<div class="container-fluid" style="margin: 10px;">
		<!-- 题干区域 -->
		<div class="row disable-selected">
			<div class="col-md-12">
			（{number}）{question_text}
			</div>
		</div>
{code_html}
{options_html}	</div>
"""
        
        extra_script = """// 接收来自宿主程序的答案
			window.answer = function(option) {
				switch(option)
				{
					case "A":
					case "B":
					case "C":
					case "D":
					case "E":
					case "F":
					case "G":
					case "H":
					case "I":
					case "J":
						$('#option' + option).attr('checked', 'true');
				}
			};"""
        
        extra_ready = """// 监听选项变化
			$('input[type="radio"][name="options"]').change(function() {
				var selectedValue = $(this).val();
				if (AppBridge.submit) {
					// 向宿主程序提交答案
					AppBridge.submit(selectedValue);
				} else {
					Toastify({
						text: "无法向宿主程序同步答案！"
					}).showToast();
				}
			});"""
        
        return (self.base_head.format(title="单选题") + body + 
                self.base_foot.format(extra_script=extra_script, extra_ready=extra_ready))
    
    def generate_fill_blank(self, number, question_text, code, choice_options):
        """生成选择填空题HTML"""
        
        # 代码区域（主代码）
        code_escaped = html.escape(code).replace('\n', '\n') if code.strip() else ''
        
        # 备选项区域
        choice_escaped = html.escape(choice_options).replace('\n', '\n') if choice_options.strip() else ''
        
        body = f"""	<div class="container-fluid" style="margin: 10px;">
		<!-- 题干区域 -->
		<div class="row disable-selected">
			<div class="col-md-12">
			{question_text}
			</div>
		</div>
		<!-- 代码区域 -->
		<div class="row" style="margin-top: 10px;">
			<div class="col-md-12">
<pre id="code-1">
{code_escaped}</pre>
			</div>
		</div>
		<div class="row" style="padding-left: 10px;">
			<button type="button" class="btn btn-primary btn-sm btncopy" data-clipboard-target="#code-1">复制代码</button>
		</div>
		<!-- 备选项区域 -->
		<div class="row disable-selected" style="margin-top: 20px;">
			<div class="col-md-12">
			备选项如下：
			</div>
		</div>
		<div class="row" style="margin-top: 10px;">
			<div class="col-md-4">
<pre id="code-2">
{choice_escaped}</pre>
			</div>
		</div>
		<div class="row" style="padding-left: 10px;">
			<button type="button" class="btn btn-primary btn-sm btncopy" data-clipboard-target="#code-2">复制代码</button>
		</div>
	</div>
"""
        
        return (self.base_head.format(title="选择填空题") + body + 
                self.base_foot.format(extra_script='', extra_ready=''))
    
    def generate_c_operation(self, question_text):
        """生成C语言操作题HTML"""
        
        body = f"""	<div class="container-fluid" style="margin: 10px;">
		<!-- 题干区域 -->
		<div class="row disable-selected">
			<div class="col-md-12">
			点击"答题"按钮，进入 prog.c 作答，根据程序功能描述，编写程序。<span style="font-weight: bold;">严禁更改 prog.c 中已有代码和注释，仅限在编程区域内编写程序，编程区域外作答无效，可根据需要自行增加或删除编程区域内的行数。</span>
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			作答完毕，保存 prog.c 文件并关闭 Dev-C++软件，点击"提交本题"按钮。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			<span style="font-weight: bold;">程序功能：</span>{question_text}
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
				程序运行结果示例如下图所示。注意：输入输出格式必须与示例一致。
			</div>
		</div>
		<!-- 图片区域 -->
		<div class="row disable-selected" style="margin-top: 10px;">
			<div class="col-md-6">
				<img class="img-responsive center-block" src="./static/img1.png" alt="图片">
			</div>
		</div>
	</div>
"""
        
        return (self.base_head.format(title="操作题") + body + 
                self.base_foot.format(extra_script='', extra_ready=''))
    
    def generate_ps_operation(self, question_text):
        """生成Photoshop操作题HTML"""
        
        body = f"""	<div class="container-fluid" style="margin: 10px;">
		<!-- 题干区域 -->
		<div class="row disable-selected">
			<div class="col-md-12">
			{question_text}
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			1．点击"答题"按钮，打开试题文件夹内的"作品.psd"文件，完成作品制作，图像尺寸及分辨率无需改动，考试结果以此文件为准。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			2．根据样图和给定的素材，制作与样图效果一致的作品。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			3．严禁使用样图去除水印作为作品提交。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			4．制作效果应与样图一致，水印不要制作。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			5．保存"作品.psd"文件（保留图层信息），存储位置不变。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			6．作答完毕，关闭 Photoshop 软件，点击"提交本题"按钮。
			</div>
		</div>
		<div class="row disable-selected">
			<div class="col-md-12">
			样图：
			</div>
		</div>
		<!-- 图片区域 -->
		<div class="row disable-selected" style="margin-top: 10px;">
			<div class="col-md-6">
				<img class="img-responsive center-block" src="./static/example.jpg" alt="样图">
			</div>
		</div>
	</div>
"""
        
        return (self.base_head.format(title="操作题") + body + 
                self.base_foot.format(extra_script='', extra_ready=''))
