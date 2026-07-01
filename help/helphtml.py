import webview

html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>说明书</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --ink: #2d1f14;
            --ink-light: #6b4c3b;
            --vermillion: #b85450;
            --vermillion-soft: #d4897a;
            --jade: #5b8c6f;
            --gold: #c4a35a;
            --rice-paper: #f8f3ea;
            --rice-paper-dark: #efe6d8;
            --card-cream: #fcf9f4;
            --shadow: rgba(45, 31, 20, 0.08);
            --shadow-hover: rgba(45, 31, 20, 0.18);

            --font-display: 'Ma Shan Zheng', 'KaiTi', 'STKaiti', cursive;
            --font-body: 'Noto Serif SC', 'SimSun', 'STSong', serif;
        }

        body {
            font-family: var(--font-body);
            background-color: var(--rice-paper);
            background-image:
                radial-gradient(ellipse at 10% 20%, rgba(196, 163, 90, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 90% 80%, rgba(91, 140, 111, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(184, 84, 80, 0.03) 0%, transparent 60%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            color: var(--ink);
            line-height: 1.8;
            -webkit-font-smoothing: antialiased;
        }

        /* ---- paper texture overlay ---- */
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 9999;
            opacity: 0.035;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
            background-repeat: repeat;
            background-size: 256px 256px;
        }

        /* ---- scrollbar ---- */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--rice-paper-dark); border-radius: 3px; }
        ::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #b8943a; }

        /* ---- container ---- */
        .scroll-container {
            max-width: 780px;
            width: 100%;
            position: relative;
            z-index: 1;
        }

        /* ---- header ---- */
        .header {
            text-align: center;
            margin-bottom: 12px;
            opacity: 0;
            animation: fadeInDown 1s ease-out 0.2s forwards;
        }

        .header h1 {
            font-family: var(--font-display);
            font-size: 54px;
            font-weight: 400;
            color: var(--ink);
            letter-spacing: 14px;
            margin-bottom: 4px;
            text-shadow: 2px 2px 4px rgba(45, 31, 20, 0.06);
        }

        .header h1 .char {
            display: inline-block;
            opacity: 0;
            animation: charAppear 0.6s ease-out forwards;
        }
        .header h1 .char:nth-child(1) { animation-delay: 0.3s; }
        .header h1 .char:nth-child(2) { animation-delay: 0.4s; }
        .header h1 .char:nth-child(3) { animation-delay: 0.5s; }

        /* decorative line under title */
        .header-decoration {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 6px 0 10px;
            opacity: 0;
            animation: fadeIn 0.8s ease-out 0.7s forwards;
        }
        .header-decoration .line {
            width: 48px;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--vermillion-soft), transparent);
        }
        .header-decoration .diamond {
            width: 6px;
            height: 6px;
            background: var(--vermillion);
            transform: rotate(45deg);
            opacity: 0.6;
        }

        .header .subtitle {
            font-family: var(--font-body);
            font-size: 15px;
            color: var(--ink-light);
            letter-spacing: 6px;
            opacity: 0;
            animation: fadeIn 0.8s ease-out 0.6s forwards;
        }

        /* ---- divider ---- */
        .divider {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin: 10px 0 22px;
            opacity: 0;
            animation: fadeIn 0.8s ease-out 0.8s forwards;
        }
        .divider .dot {
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: var(--gold);
            opacity: 0.4;
        }
        .divider .line {
            width: 32px;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--gold), transparent);
        }

        /* ---- carousel wrapper ---- */
        .carousel-wrapper {
            position: relative;
            opacity: 0;
            animation: fadeInUp 1s ease-out 0.9s forwards;
        }

        .carousel {
            display: flex;
            gap: 20px;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            padding: 12px 8px 24px;
            -webkit-overflow-scrolling: touch;
        }

        .carousel::-webkit-scrollbar { height: 4px; }
        .carousel::-webkit-scrollbar-track { background: transparent; }
        .carousel::-webkit-scrollbar-thumb {
            background: linear-gradient(90deg, var(--vermillion-soft), var(--gold));
            border-radius: 2px;
        }

        /* ---- card ---- */
        .card {
            flex: 0 0 280px;
            scroll-snap-align: start;
            background: var(--card-cream);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px var(--shadow);
            border: 1px solid rgba(196, 163, 90, 0.18);
            transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1),
                        box-shadow 0.5s cubic-bezier(0.22, 1, 0.36, 1);
            will-change: transform;
            position: relative;
        }

        .card::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            pointer-events: none;
        }

        .card:hover {
            transform: translateY(-6px);
            box-shadow: 0 12px 36px var(--shadow-hover);
        }

        /* card header image area */
        .card-image {
            width: 100%;
            height: 190px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 52px;
            position: relative;
            overflow: hidden;
            transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
        }

        .card:hover .card-image {
            transform: scale(1.03);
        }

        .card-image .wash {
            position: absolute;
            inset: 0;
            opacity: 0.12;
            transition: opacity 0.6s ease;
        }
        .card:hover .card-image .wash {
            opacity: 0.18;
        }

        .card-image .icon {
            position: relative;
            z-index: 1;
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.08));
            transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        }
        .card:hover .card-image .icon {
            transform: scale(1.08);
        }

        /* card body */
        .card-body {
            padding: 18px 20px 22px;
            position: relative;
        }

        .card-body h3 {
            font-family: var(--font-display);
            font-size: 22px;
            font-weight: 400;
            color: var(--ink);
            letter-spacing: 4px;
            margin-bottom: 4px;
        }

        .card-body .poem {
            font-family: var(--font-body);
            font-size: 13px;
            color: var(--ink-light);
            line-height: 1.9;
            letter-spacing: 1px;
        }

        .card-body .poem .highlight {
            color: var(--vermillion);
            font-weight: 600;
        }

        /* seal stamp decoration */
        .card-seal {
            position: absolute;
            bottom: 18px;
            right: 20px;
            width: 32px;
            height: 32px;
            border: 2px solid var(--vermillion);
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-size: 14px;
            color: var(--vermillion);
            opacity: 0.5;
            transform: rotate(4deg);
            transition: opacity 0.4s ease;
        }
        .card:hover .card-seal {
            opacity: 0.8;
        }

        /* ---- nav buttons ---- */
        .btn-group {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 24px;
            margin-top: 4px;
            opacity: 0;
            animation: fadeIn 0.8s ease-out 1.1s forwards;
        }

        .btn-group button {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            border: 1px solid rgba(196, 163, 90, 0.35);
            background: var(--card-cream);
            color: var(--ink-light);
            font-size: 16px;
            cursor: pointer;
            transition: all 0.35s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-body);
        }

        .btn-group button:hover {
            background: var(--vermillion);
            color: #fff;
            border-color: var(--vermillion);
            box-shadow: 0 4px 14px rgba(184, 84, 80, 0.25);
        }

        .btn-group button:active {
            transform: scale(0.92);
        }

        .btn-group .track-wrap {
            position: relative;
            width: 200px;
            height: 4px;
            background: rgba(107, 76, 59, 0.12);
            border-radius: 2px;
            overflow: hidden;
            cursor: pointer;
        }
        .btn-group .track-wrap .thumb {
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 48px;
            background: linear-gradient(90deg, var(--vermillion-soft), var(--vermillion));
            border-radius: 2px;
            transition: none;
            will-change: transform;
        }

        /* ---- scroll hint ---- */
        .scroll-hint {
            text-align: center;
            margin-top: 14px;
            font-size: 12px;
            color: var(--ink-light);
            letter-spacing: 2px;
            opacity: 0.4;
            animation: fadeIn 1s ease-out 1.4s forwards, pulse 2.5s ease-in-out 1.4s infinite;
        }
        .scroll-hint span {
            display: inline-block;
            animation: floatArrow 2s ease-in-out infinite;
        }

        /* ---- keyframes ---- */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes charAppear {
            0% { opacity: 0; transform: translateY(-8px) scale(0.95); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.6; }
        }

        @keyframes floatArrow {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(3px); }
        }
    </style>
</head>
<body>

<div class="scroll-container">

    <!-- header -->
    <div class="header">
        <h1>
            <span class="char">雅</span>
            <span class="char">集</span>
            <span class="char">·</span>
        </h1>
        <div class="header-decoration">
            <span class="line"></span>
            <span class="diamond"></span>
            <span class="line"></span>
        </div>
        <p class="subtitle">国 风 · 物 语</p>
    </div>

    <!-- divider -->
    <div class="divider">
        <span class="line"></span>
        <span class="dot"></span>
        <span class="line"></span>
    </div>

    <!-- carousel -->
    <div class="carousel-wrapper">
        <div class="carousel" id="carousel">

            <!-- 灯笼 -->
            <div class="card">
                <div class="card-image" style="background: linear-gradient(145deg, #f5ebe0, #ead8c8);">
                    <div class="wash" style="background: radial-gradient(ellipse at 30% 40%, rgba(184,84,80,0.15), transparent 60%);"></div>
                    <span class="icon" style="font-size: 56px;">🏮</span>
                </div>
                <div class="card-body">
                    <h3>灯 笼</h3>
                    <p class="poem">
                        朱红纱笼 · 烛影摇红<br>
                        元宵佳节 · <span class="highlight">万家灯火</span>映长街
                    </p>
                    <div class="card-seal">灯</div>
                </div>
            </div>

            <!-- 茶道 -->
            <div class="card">
                <div class="card-image" style="background: linear-gradient(145deg, #e8f0e4, #d4e0ce);">
                    <div class="wash" style="background: radial-gradient(ellipse at 60% 40%, rgba(91,140,111,0.12), transparent 60%);"></div>
                    <span class="icon" style="font-size: 56px;">🍵</span>
                </div>
                <div class="card-body">
                    <h3>茶 道</h3>
                    <p class="poem">
                        一壶春雪 · 满室兰香<br>
                        静坐烹茶 · <span class="highlight">品味山水</span>之韵
                    </p>
                    <div class="card-seal">茶</div>
                </div>
            </div>

            <!-- 竹韵 -->
            <div class="card">
                <div class="card-image" style="background: linear-gradient(145deg, #e8ece0, #d6dcc8);">
                    <div class="wash" style="background: radial-gradient(ellipse at 40% 50%, rgba(91,140,111,0.10), transparent 60%);"></div>
                    <span class="icon" style="font-size: 56px;">🎋</span>
                </div>
                <div class="card-body">
                    <h3>竹 韵</h3>
                    <p class="poem">
                        疏影横斜 · 清风徐来<br>
                        <span class="highlight">虚怀若谷</span> · 君子之风
                    </p>
                    <div class="card-seal">竹</div>
                </div>
            </div>

            <!-- 花信 -->
            <div class="card">
                <div class="card-image" style="background: linear-gradient(145deg, #f5e8e8, #ebd6d0);">
                    <div class="wash" style="background: radial-gradient(ellipse at 50% 30%, rgba(212,137,122,0.14), transparent 60%);"></div>
                    <span class="icon" style="font-size: 56px;">🌸</span>
                </div>
                <div class="card-body">
                    <h3>花 信</h3>
                    <p class="poem">
                        桃之夭夭 · 灼灼其华<br>
                        春风十里 · <span class="highlight">不如花间</span>一壶酒
                    </p>
                    <div class="card-seal">花</div>
                </div>
            </div>

            <!-- 山水 -->
            <div class="card">
                <div class="card-image" style="background: linear-gradient(145deg, #dde4dc, #cad4c4);">
                    <div class="wash" style="background: radial-gradient(ellipse at 30% 60%, rgba(91,140,111,0.12), transparent 60%);"></div>
                    <span class="icon" style="font-size: 56px;">⛰️</span>
                </div>
                <div class="card-body">
                    <h3>山 水</h3>
                    <p class="poem">
                        远山如黛 · 近水含烟<br>
                        水墨丹青 · <span class="highlight">写不尽</span>江山如画
                    </p>
                    <div class="card-seal">山</div>
                </div>
            </div>

        </div>
    </div>

    <!-- nav buttons -->
    <div class="btn-group">
        <button onclick="scrollCarousel(-1)" aria-label="上一张">‹</button>
        <div class="track-wrap" id="track">
            <div class="thumb" id="thumb"></div>
        </div>
        <button onclick="scrollCarousel(1)" aria-label="下一张">›</button>
    </div>

    <!-- scroll hint -->
    <div class="scroll-hint">
        <span>‹</span> 左右滑动浏览 <span>›</span>
    </div>

</div>

<script>
    function scrollCarousel(dir) {
        const el = document.getElementById('carousel');
        const card = el.querySelector('.card');
        if (!card) return;
        const gap = parseFloat(getComputedStyle(el).gap) || 20;
        const step = card.offsetWidth + gap;
        el.scrollBy({ left: dir * step, behavior: 'smooth' });
    }

    // 卷轴游标指示器 — 比例平滑滑动
    const carousel = document.getElementById('carousel');
    const thumb = document.getElementById('thumb');

    function updateThumb() {
        const maxScroll = carousel.scrollWidth - carousel.clientWidth;
        const ratio = maxScroll > 0 ? carousel.scrollLeft / maxScroll : 0;
        const track = thumb.parentElement;
        const maxTravel = track.offsetWidth - thumb.offsetWidth;
        thumb.style.transform = 'translateX(' + (ratio * maxTravel) + 'px)';
    }

    carousel.addEventListener('scroll', updateThumb);
    window.addEventListener('resize', updateThumb);
    updateThumb();
</script>

</body>
</html>
"""

window = webview.create_window('说明书', html=html_content, width=1000, height=800, resizable=False)
webview.start()
