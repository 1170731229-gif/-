from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sys
import os
from datetime import datetime, timedelta
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantplus import (
    QuantPlus,
    DailyT0Strategy,
    GridT0Strategy,
    VolatilityT0Strategy,
    EnhancedT0Strategy,
    GridT0StrategyAdvanced,
    TrendT0Strategy,
    run_backtest
)

app = FastAPI(title="QuantPlus 量化交易平台")

html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuantPlus 量化交易平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Microsoft YaHei", Arial, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; color: #00d4ff; font-size: 2.5em; margin-bottom: 10px; text-shadow: 0 0 20px rgba(0,212,255,0.5); }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; margin-bottom: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
        .card h2 { color: #00d4ff; margin-bottom: 20px; font-size: 1.3em; display: flex; align-items: center; gap: 10px; }
        .card h2 .badge { background: #ff6b6b; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 12px; }
        .card h2 .auto-badge { background: #00ff88; color: #000; padding: 3px 10px; border-radius: 20px; font-size: 12px; }
        .form-row { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px; }
        .form-group { flex: 1; min-width: 200px; }
        label { display: block; margin-bottom: 8px; color: #aaa; }
        input, select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); color: #fff; font-size: 16px; }
        input:focus, select:focus { outline: none; border-color: #00d4ff; box-shadow: 0 0 10px rgba(0,212,255,0.3); }
        .btn-group { display: flex; gap: 15px; flex-wrap: wrap; margin-top: 20px; }
        .btn { padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: all 0.3s; font-weight: bold; }
        .btn-primary { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #fff; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,212,255,0.4); }
        .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
        .btn-secondary:hover { background: rgba(255,255,255,0.2); }
        .btn-warning { background: linear-gradient(135deg, #ffa500, #ff8c00); color: #fff; }
        .btn-warning:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(255,165,0,0.4); }
        .btn-success { background: linear-gradient(135deg, #00ff88, #00cc66); color: #000; }
        .btn-success:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,255,136,0.4); }
        .btn-danger { background: linear-gradient(135deg, #ff4444, #cc0000); color: #fff; }
        .btn-danger:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(255,68,68,0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .output { background: #0d1117; border-radius: 10px; padding: 20px; min-height: 400px; max-height: 600px; overflow-y: auto; font-family: "Consolas", monospace; font-size: 14px; line-height: 1.6; }
        .output pre { white-space: pre-wrap; word-wrap: break-word; }
        .result-card { background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,153,204,0.1)); border: 1px solid rgba(0,212,255,0.3); border-radius: 10px; padding: 20px; margin-top: 20px; }
        .result-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .result-item:last-child { border-bottom: none; }
        .result-label { color: #888; }
        .result-value { font-weight: bold; color: #00d4ff; font-size: 1.1em; }
        .positive { color: #00ff88 !important; }
        .negative { color: #ff4444 !important; }
        .loading { text-align: center; padding: 20px; }
        .spinner { width: 40px; height: 40px; border: 4px solid rgba(0,212,255,0.3); border-top-color: #00d4ff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .info { background: rgba(0,212,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #00d4ff; }
        .strategy-desc { font-size: 12px; color: #888; margin-top: 5px; }
        .tip { background: rgba(255,170,0,0.1); padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 12px; color: #ffaacc; }
        .recommend-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
        .stock-card { background: rgba(255,255,255,0.05); border-radius: 10px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s; }
        .stock-card:hover { background: rgba(255,255,255,0.1); border-color: #00d4ff; }
        .stock-card .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .stock-card .code { font-weight: bold; color: #00d4ff; }
        .stock-card .name { color: #888; font-size: 14px; }
        .stock-card .score { background: linear-gradient(135deg, #00ff88, #00cc66); color: #000; padding: 3px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
        .stock-card .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px; }
        .stock-card .metric { display: flex; justify-content: space-between; }
        .stock-card .metric-label { color: #666; }
        .stock-card .metric-value { color: #fff; font-weight: bold; }
        .stock-card .action-btn { width: 100%; margin-top: 10px; padding: 8px; font-size: 13px; }
        .stock-card .progress { width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 10px; overflow: hidden; }
        .stock-card .progress-bar { height: 100%; background: #00d4ff; transition: width 0.3s; }
        .empty-msg { text-align: center; padding: 40px; color: #666; }
        .rank-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .rank-table th, .rank-table td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .rank-table th { background: rgba(0,212,255,0.1); color: #00d4ff; }
        .rank-table tr:hover { background: rgba(255,255,255,0.05); }
        .rank-table .rank { font-weight: bold; color: #00d4ff; }
        .rank-table .profit { font-weight: bold; }
        .toggle-row { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
        .toggle { position: relative; width: 50px; height: 26px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.2); border-radius: 26px; transition: 0.3s; }
        .toggle-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s; }
        .toggle input:checked + .toggle-slider { background: #00ff88; }
        .toggle input:checked + .toggle-slider:before { transform: translateX(24px); }
        .auto-status { padding: 8px 15px; border-radius: 20px; font-size: 12px; display: inline-flex; align-items: center; gap: 5px; }
        .auto-status.running { background: rgba(0,255,136,0.2); color: #00ff88; }
        .auto-status.stopped { background: rgba(255,255,255,0.1); color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>QuantPlus</h1>
        <p class="subtitle">A股做T策略量化回测平台</p>

        <div class="card">
            <h2><span class="badge">NEW</span> 每日做T推荐</h2>
            <div class="info">系统根据振幅、流动性、波动率等指标自动筛选适合做T的股票，支持自动批量回测</div>
            <div class="form-row">
                <div class="form-group">
                    <label>筛选数量</label>
                    <select id="recomCount">
                        <option value="6">6只</option>
                        <option value="10" selected>10只</option>
                        <option value="20">20只</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>市场范围</label>
                    <select id="market">
                        <option value="all" selected>全部A股</option>
                        <option value="sh">上证主板</option>
                        <option value="sz">深证主板</option>
                        <option value="etf">ETF基金</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>初始资金 (元)</label>
                    <input type="number" id="autoCash" value="20000" min="1000" step="1000">
                </div>
                <div class="form-group">
                    <label>做T策略</label>
                    <select id="autoStrategy">
                        <option value="EnhancedT0Strategy">增强型做T</option>
                        <option value="DailyT0Strategy">每日做T基础版</option>
                        <option value="GridT0Strategy">网格做T</option>
                        <option value="VolatilityT0Strategy">波动率做T</option>
                        <option value="TrendT0Strategy">趋势跟踪做T</option>
                    </select>
                </div>
            </div>
            <div class="toggle-row">
                <label class="toggle">
                    <input type="checkbox" id="autoRun">
                    <span class="toggle-slider"></span>
                </label>
                <span>自动运行推荐股票批量回测</span>
                <span class="auto-status stopped" id="autoStatus">空闲</span>
            </div>
            <div class="btn-group">
                <button class="btn btn-success" id="recomBtn" onclick="startRecommend()">🚀 开始智能筛选</button>
                <button class="btn btn-danger" id="stopBtn" onclick="stopAuto()" style="display:none;">⏹ 停止</button>
            </div>
            <div class="recommend-list" id="recommendList" style="margin-top: 20px;">
                <div class="empty-msg">点击上方按钮开始智能筛选</div>
            </div>
            <div id="rankSection" style="display: none; margin-top: 20px;">
                <h3 style="color: #00d4ff; margin-bottom: 15px;">🏆 回测收益率排行榜</h3>
                <table class="rank-table" id="rankTable">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>代码</th>
                            <th>名称</th>
                            <th>评分</th>
                            <th>收益率</th>
                            <th>收益额</th>
                            <th>最终资金</th>
                        </tr>
                    </thead>
                    <tbody id="rankBody"></tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>手动回测</h2>
            <div class="form-row">
                <div class="form-group">
                    <label>股票代码</label>
                    <input type="text" id="symbol" value="002475" placeholder="如: 002475, 600519">
                </div>
                <div class="form-group">
                    <label>数据源</label>
                    <select id="source">
                        <option value="baostock">Baostock (免费)</option>
                        <option value="akshare">Akshare</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>数据级别</label>
                    <select id="period">
                        <option value="daily">日线</option>
                        <option value="5">5分钟</option>
                        <option value="15">15分钟</option>
                        <option value="30">30分钟</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>初始资金 (元)</label>
                    <input type="number" id="cash" value="20000" min="1000" step="1000">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>做T策略</label>
                    <select id="strategy">
                        <option value="EnhancedT0Strategy">增强型做T (推荐)</option>
                        <option value="DailyT0Strategy">每日做T基础版</option>
                        <option value="GridT0Strategy">网格做T</option>
                        <option value="GridT0StrategyAdvanced">高级网格做T</option>
                        <option value="VolatilityT0Strategy">波动率做T</option>
                        <option value="TrendT0Strategy">趋势跟踪做T</option>
                    </select>
                    <div class="strategy-desc" id="strategyDesc">正T+反T双模式，结合均价线与MACD背离</div>
                </div>
            </div>
            <div class="btn-group">
                <button class="btn btn-primary" id="fetchBtn" onclick="fetchData()">获取数据</button>
                <button class="btn btn-primary" id="backtestBtn" onclick="runBacktest()" disabled>运行回测</button>
                <button class="btn btn-secondary" onclick="clearOutput()">清空</button>
            </div>
        </div>

        <div class="card">
            <h2>输出结果</h2>
            <div class="output" id="output"><pre>等待操作...</pre></div>
        </div>

        <div class="result-card" id="resultCard" style="display: none;">
            <h2 style="color: #00d4ff; margin-bottom: 15px;">回测结果</h2>
            <div class="result-item">
                <span class="result-label">初始资金</span>
                <span class="result-value" id="resCash">-</span>
            </div>
            <div class="result-item">
                <span class="result-label">最终资金</span>
                <span class="result-value" id="resFinal">-</span>
            </div>
            <div class="result-item">
                <span class="result-label">收益</span>
                <span class="result-value" id="resProfit">-</span>
            </div>
            <div class="result-item">
                <span class="result-label">收益率</span>
                <span class="result-value" id="resPct">-</span>
            </div>
        </div>
    </div>

    <script>
        const strategyDesc = {
            'EnhancedT0Strategy': '正T+反T双模式，结合均价线与MACD背离，单次做T不超底仓1/3',
            'DailyT0Strategy': '基于RSI和波动率的简单做T，每日最多2次',
            'GridT0Strategy': '预设价格网格，跌破买入涨破卖出',
            'GridT0StrategyAdvanced': '多层级网格策略，适合震荡市',
            'VolatilityT0Strategy': '基于历史波动率的动态做T',
            'TrendT0Strategy': '趋势跟踪，EMA均线判断顺势做T'
        };

        document.getElementById('strategy').addEventListener('change', function() {
            document.getElementById('strategyDesc').textContent = strategyDesc[this.value] || '';
        });

        let currentData = null;
        let autoRunning = false;
        let autoResults = [];
        let currentStocks = [];

        function log(msg) {
            const output = document.getElementById('output');
            const pre = output.querySelector('pre') || document.createElement('pre');
            if (!output.contains(pre)) output.appendChild(pre);
            pre.innerHTML += msg + '\\n';
            output.scrollTop = output.scrollHeight;
        }

        function showLoading(show) {
            const output = document.getElementById('output');
            if (show) {
                output.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top:15px">处理中...</p></div>';
            }
        }

        function clearOutput() {
            document.getElementById('output').innerHTML = '<pre>等待操作...</pre>';
            document.getElementById('resultCard').style.display = 'none';
            currentData = null;
            document.getElementById('backtestBtn').disabled = true;
        }

        function updateAutoStatus(running, text) {
            const status = document.getElementById('autoStatus');
            status.textContent = text;
            status.className = 'auto-status ' + (running ? 'running' : 'stopped');
            document.getElementById('stopBtn').style.display = running ? 'inline-block' : 'none';
            document.getElementById('recomBtn').disabled = running;
        }

        async function startRecommend() {
            const cash = parseFloat(document.getElementById('autoCash').value);
            const strategy = document.getElementById('autoStrategy').value;
            const total = stocks.length;
            let completed = 0;

            // 构造批量任务并提交到后端批量回测接口
            const jobs = stocks.map(s => ({ symbol: s.code, source: 'baostock', period: 'daily', cash, strategy }));
            updateAutoStatus(true, `回测中 ${completed}/${total}`);
            try {
                const resp = await fetch('/api/backtest_batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jobs })
                });
                const data = await resp.json();
                if (data.success && Array.isArray(data.results)) {
                    for (const r of data.results) {
                        if (!autoRunning) break;
                        if (r.success) {
                            const s = stocks.find(x => x.code === r.symbol) || { name: r.symbol, score: 0 };
                            autoResults.push({ code: r.symbol, name: s.name, score: s.score, profit: r.profit, profit_pct: r.profit_pct, final_value: r.final_value });
                            log('\n✅ ' + s.name + ' 收益率: ' + (r.profit_pct >= 0 ? '+' : '') + r.profit_pct.toFixed(2) + '%');
                        } else {
                            log('\n❌ ' + (r.symbol || '') + ' 回测失败: ' + (r.error || ''));
                        }
                        completed++;
                        updateProgress(r.symbol || '', completed / total * 100);
                        updateAutoStatus(true, `回测中 ${completed}/${total}`);
                    }

                    if (autoResults.length > 0) {
                        autoResults.sort((a, b) => b.profit_pct - a.profit_pct);
                        showRankTable();
                        log('\n🏆 最佳选择: ' + autoResults[0].name + ' 收益率 ' + autoResults[0].profit_pct.toFixed(2) + '%');
                    }
                } else {
                    log('\n批量回测失败: ' + (data.error || '未知错误'));
                }
            } catch (e) {
                log('\n批量回测请求失败: ' + e.message);
            }

            updateAutoStatus(false, '完成');
            autoRunning = false;
        }

                    if (fetchData.success) {
                        const backtestRes = await fetch('/api/backtest', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ data: fetchData.data, cash, strategy })
                        });
                        const result = await backtestRes.json();

                        if (result.success) {
                            autoResults.push({
                                code: s.code,
                                name: s.name,
                                score: s.score,
                                profit: result.profit,
                                profit_pct: result.profit_pct,
                                final_value: result.final_value
                            });
                            log('✅ ' + s.name + ' 收益率: ' + (result.profit_pct >= 0 ? '+' : '') + result.profit_pct.toFixed(2) + '%');
                        }
                    }
                } catch (e) {
                    log('❌ ' + s.code + ' 回测失败');
                }

                completed++;
                updateProgress(s.code, completed / total * 100);
            }

            if (autoResults.length > 0) {
                autoResults.sort((a, b) => b.profit_pct - a.profit_pct);
                showRankTable();
                log('\\n🏆 最佳选择: ' + autoResults[0].name + ' 收益率 ' + autoResults[0].profit_pct.toFixed(2) + '%');
            }

            updateAutoStatus(false, '完成');
            autoRunning = false;
        }

        function stopAuto() {
            autoRunning = false;
            updateAutoStatus(false, '已停止');
            log('\\n⏹ 已停止自动回测');
        }

        function updateProgress(code, pct) {
            const card = document.querySelector('[data-code="' + code + '"]');
            if (card) {
                const progressBar = card.querySelector('.progress-bar');
                if (progressBar) progressBar.style.width = pct + '%';
            }
        }

        function showRankTable() {
            const tbody = document.getElementById('rankBody');
            tbody.innerHTML = '';
            autoResults.forEach((r, i) => {
                const profitClass = r.profit >= 0 ? 'positive' : 'negative';
                tbody.innerHTML += `
                    <tr>
                        <td class="rank">${i + 1}</td>
                        <td>${r.code}</td>
                        <td>${r.name}</td>
                        <td>${r.score}分</td>
                        <td class="profit ${profitClass}">${r.profit_pct >= 0 ? '+' : ''}${r.profit_pct.toFixed(2)}%</td>
                        <td class="${profitClass}">${r.profit >= 0 ? '+' : ''}${r.profit.toFixed(0)}元</td>
                        <td>${r.final_value.toFixed(0)}元</td>
                    </tr>
                `;
            });
            document.getElementById('rankSection').style.display = 'block';
        }

        function renderRecommendList(stocks) {
            if (!stocks || stocks.length === 0) {
                document.getElementById('recommendList').innerHTML = '<div class="empty-msg">暂无符合条件的股票</div>';
                return;
            }

            autoRunning = true;
            let html = '';
            stocks.forEach(s => {
                const priceChange = s.price_change >= 0 ? '+' + s.price_change.toFixed(2) : s.price_change.toFixed(2);
                const changeColor = s.price_change >= 0 ? 'positive' : 'negative';
                html += `
                <div class="stock-card" data-code="${s.code}">
                    <div class="header">
                        <div>
                            <div class="code">${s.code}</div>
                            <div class="name">${s.name}</div>
                        </div>
                        <div class="score">${s.score}分</div>
                    </div>
                    <div class="metrics">
                        <div class="metric">
                            <span class="metric-label">最新价</span>
                            <span class="metric-value">${s.price.toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">涨跌幅</span>
                            <span class="metric-value ${changeColor}">${priceChange}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">振幅</span>
                            <span class="metric-value">${s.amplitude.toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">成交额(万)</span>
                            <span class="metric-value">${(s.amount / 10000).toFixed(0)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">波动率</span>
                            <span class="metric-value">${s.volatility.toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">换手率</span>
                            <span class="metric-value">${s.turnover.toFixed(2)}%</span>
                        </div>
                    </div>
                    <div class="progress"><div class="progress-bar" style="width: 0%"></div></div>
                </div>
                `;
            });
            document.getElementById('recommendList').innerHTML = html;
        }

        async function fetchData() {
            const symbol = document.getElementById('symbol').value.trim();
            const source = document.getElementById('source').value;
            const period = document.getElementById('period').value;

            if (!symbol) { alert('请输入股票代码'); return; }

            document.getElementById('fetchBtn').disabled = true;
            document.getElementById('backtestBtn').disabled = true;
            showLoading(true);

            try {
                const response = await fetch('/api/fetch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol, source, period })
                });
                const data = await response.json();

                if (data.success) {
                    currentData = data.data;
                    document.getElementById('output').innerHTML = '<pre>' + data.log + '</pre>';
                    document.getElementById('backtestBtn').disabled = false;
                } else {
                    document.getElementById('output').innerHTML = '<pre style="color:#ff4444">错误: ' + data.error + '</pre>';
                }
            } catch (e) {
                document.getElementById('output').innerHTML = '<pre style="color:#ff4444">请求失败: ' + e.message + '</pre>';
            } finally {
                document.getElementById('fetchBtn').disabled = false;
            }
        }

        async function runBacktest() {
            if (!currentData) { alert('请先获取数据'); return; }

            const cash = parseFloat(document.getElementById('cash').value);
            const strategy = document.getElementById('strategy').value;

            document.getElementById('backtestBtn').disabled = true;
            showLoading(true);

            try {
                const response = await fetch('/api/backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ data: currentData, cash, strategy })
                });
                const result = await response.json();

                if (result.success) {
                    document.getElementById('output').innerHTML = '<pre>' + result.log + '</pre>';

                    document.getElementById('resCash').textContent = cash.toLocaleString() + ' 元';
                    document.getElementById('resFinal').textContent = result.final_value.toLocaleString() + ' 元';
                    document.getElementById('resProfit').textContent = result.profit.toLocaleString() + ' 元';
                    document.getElementById('resPct').textContent = (result.profit_pct >= 0 ? '+' : '') + result.profit_pct.toFixed(2) + '%';

                    const profitEl = document.getElementById('resProfit');
                    const pctEl = document.getElementById('resPct');
                    profitEl.className = 'result-value ' + (result.profit >= 0 ? 'positive' : 'negative');
                    pctEl.className = 'result-value ' + (result.profit >= 0 ? 'positive' : 'negative');

                    document.getElementById('resultCard').style.display = 'block';
                } else {
                    document.getElementById('output').innerHTML = '<pre style="color:#ff4444">错误: ' + result.error + '</pre>';
                }
            } catch (e) {
                document.getElementById('output').innerHTML = '<pre style="color:#ff4444">请求失败: ' + e.message + '</pre>';
            } finally {
                document.getElementById('backtestBtn').disabled = false;
            }
        }
    </script>
</body>
</html>
"""

# 简单内存缓存，避免短时间内重复抓取同一只股票的数据
from time import time
_data_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 600  # 秒

# 可配置项（环境变量可覆盖）
import logging
import json
import hashlib
import os

MAX_FETCH_WORKERS = int(os.environ.get("MAX_FETCH_WORKERS", "8"))
MAX_BACKTEST_WORKERS = int(os.environ.get("MAX_BACKTEST_WORKERS", "2"))
_BACKTEST_CACHE = {}
_BACKTEST_CACHE_LOCK = threading.Lock()

# 日志
logger = logging.getLogger("quantplus_web")
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.INFO)



class FetchRequest(BaseModel):
    symbol: str
    source: str = "baostock"
    period: str = "daily"


class BacktestRequest(BaseModel):
    data: dict
    cash: float = 20000
    strategy: str = "EnhancedT0Strategy"


class BacktestJob(BaseModel):
    symbol: str
    source: str = "baostock"
    period: str = "daily"
    cash: float = 20000
    strategy: str = "EnhancedT0Strategy"


class BacktestBatchRequest(BaseModel):
    jobs: list


class RecommendRequest(BaseModel):
    count: int = 10
    market: str = "all"


@app.get("/", response_class=HTMLResponse)
async def root():
    return html_content


@app.post("/api/recommend")
async def api_recommend(req: RecommendRequest):
    try:
        import pandas as pd
        import numpy as np

        qp = QuantPlus("baostock")

        etf_lists = {
            "sh": ["510050", "510300", "510500", "512000", "512100", "513500", "515000", "515050", "518880", "159920"],
            "sz": ["159915", "159919", "159905", "159901", "159902", "159928", "159605", "159995", "159941", "159817"],
            "all": ["510050", "510300", "510500", "512000", "512100", "513500", "515000", "515050", "518880", "159920",
                    "159915", "159919", "159905", "159901", "159902", "159928", "159605", "159995", "159941", "159817",
                    "159928", "159996", "159938", "159745", "159992", "159628", "159755", "159869", "159792", "159865"]
        }

        if req.market == "etf":
            stock_lists = etf_lists
        else:
            stock_lists = {
                "sh": ["600519", "601318", "600036", "600276", "601888", "600887", "600030", "601166", "601398", "601012"],
                "sz": ["000858", "000333", "002475", "000651", "300750", "002594", "300015", "002415", "000568", "300760"],
                "all": ["600519", "601318", "600036", "600276", "601888", "000858", "000333", "002475", "000651", "300750",
                        "600887", "600030", "601166", "601398", "601012", "002594", "300015", "002415", "000568", "300760",
                        "600028", "601668", "601288", "601328", "600050", "601186", "601857", "601088", "601138", "601360"]
            }

        codes = stock_lists.get(req.market if req.market != "etf" else "all", stock_lists["all"])[:req.count + 10]

        results = []
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

        name_map = {
            "600519": "贵州茅台", "601318": "中国平安", "600036": "招商银行", "600276": "恒瑞医药",
            "601888": "中国中免", "600887": "伊利股份", "600030": "中信证券", "601166": "兴业银行",
            "601398": "工商银行", "601012": "隆基绿能", "000858": "五粮液", "000333": "美的集团",
            "002475": "立讯精密", "000651": "格力电器", "300750": "宁德时代", "002594": "比亚迪",
            "300015": "爱尔眼科", "002415": "海康威视", "000568": "泸州老窖", "300760": "迈瑞医疗",
            "600028": "中国石化", "601668": "中国建筑", "601288": "农业银行", "601328": "交通银行",
            "600050": "中国联通", "601186": "中国铁建", "601857": "中国石油", "601088": "中国神华",
            "601138": "工业富联", "601360": "三六零",
            "510050": "50ETF", "510300": "300ETF", "510500": "500ETF", "512000": "证券ETF",
            "512100": "医疗ETF", "513500": "纳指ETF", "515000": "科技ETF", "515050": "通信ETF",
            "518880": "黄金ETF", "159920": "恒生ETF", "159915": "创业板ETF", "159919": "深100ETF",
            "159905": "深红利ETF", "159901": "深证100ETF", "159902": "中小板ETF", "159928": "消费ETF",
            "159605": "油气ETF", "159995": "芯片ETF", "159941": "恒生科技ETF", "159817": "双创ETF",
            "159996": "家电ETF", "159938": "农业ETF", "159745": "光伏ETF", "159992": "医疗设备ETF",
            "159628": "消费电子ETF", "159755": "游戏ETF", "159869": "动漫游戏ETF", "159792": "人工智能ETF",
            "159865": "机器人ETF"
        }

        # 并发抓取日线数据以减少网络等待
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _fetch_code(c):
            try:
                qp_thread = QuantPlus("baostock")
                df_local = qp_thread.source.get_daily(c, start_date, end_date)
                return c, df_local
            except Exception:
                return c, None

        max_workers = min(MAX_FETCH_WORKERS, len(codes)) if codes else 1
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_fetch_code, c): c for c in codes}
            for fut in as_completed(futures):
                code, df = fut.result()
                try:
                    if df is None or len(df) < 20:
                        continue

                    recent = df.tail(20)

                    price = df['close'].iloc[-1]
                    high_price = df['high'].iloc[-1]
                    low_price = df['low'].iloc[-1]
                    amount = df['amount'].iloc[-1]

                    price_change = ((price - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0
                    amplitude = ((high_price - low_price) / low_price * 100) if low_price > 0 else 0

                    returns = recent['close'].pct_change().dropna()
                    volatility = returns.std() * 100 * np.sqrt(20)

                    volume = df['volume'].iloc[-1] if 'volume' in df.columns else 0
                    turnover = (volume / 10000.0) if price > 0 else 0

                    avg_amplitude = ((recent['high'] - recent['low']) / recent['low'] * 100).mean()

                    if amplitude < 1.5 or amount < 10000000:
                        continue

                    score = 0
                    if amplitude >= 3: score += 30
                    elif amplitude >= 2: score += 20
                    elif amplitude >= 1.5: score += 10

                    if amount >= 500000000: score += 25
                    elif amount >= 200000000: score += 15
                    elif amount >= 100000000: score += 10

                    if volatility >= 2: score += 25
                    elif volatility >= 1.5: score += 15
                    elif volatility >= 1: score += 10

                    if abs(price_change) <= 5: score += 10
                    if avg_amplitude >= 2: score += 10

                    score = min(100, score)

                    results.append({
                        "code": code,
                        "name": name_map.get(code, code),
                        "price": float(price),
                        "price_change": float(price_change),
                        "amplitude": float(amplitude),
                        "amount": float(amount),
                        "volatility": float(volatility),
                        "turnover": float(min(turnover, 20)),
                        "score": int(score)
                    })

                except Exception:
                    continue

        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:req.count]

        return {"success": True, "stocks": results}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/fetch")
async def api_fetch(req: FetchRequest):
    try:
        # 尝试从内存缓存读取
        cache_key = (req.source, req.symbol, req.period)
        with _cache_lock:
            cached = _data_cache.get(cache_key)
            if cached and time() - cached["ts"] < _CACHE_TTL:
                return {"success": True, "data": cached["data"], "log": cached.get("log", "(cached)")}

        qp = QuantPlus(req.source)

        if req.period == "daily":
            df = qp.fetch(req.symbol)
        else:
            df = qp.fetch_minute(req.symbol, period=req.period, days=30)

        if df is None or len(df) == 0:
            return {"success": False, "error": "未获取到数据"}

        data = {
            "datetime": df["datetime"].astype(str).tolist(),
            "open": df["open"].tolist(),
            "high": df["high"].tolist(),
            "low": df["low"].tolist(),
            "close": df["close"].tolist(),
            "volume": df["volume"].tolist()
        }

        log_lines = []
        log_lines.append("=" * 50)
        log_lines.append(f"股票: {req.symbol}")
        log_lines.append(f"数据源: {req.source}")
        log_lines.append(f"数据级别: {'日线' if req.period == 'daily' else req.period + '分钟'}")
        log_lines.append(f"数据条数: {len(df)}")
        log_lines.append(f"时间范围: {df['datetime'].min()} 至 {df['datetime'].max()}")
        log_lines.append(f"最新价: {df['close'].iloc[-1]:.2f}")
        log_lines.append("=" * 50)
        log_lines.append("数据获取成功！可以运行回测")

        log_text = "\n".join(log_lines)

        # 写入缓存
        with _cache_lock:
            _data_cache[cache_key] = {"ts": time(), "data": data, "log": log_text}

        return {"success": True, "data": data, "log": log_text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/backtest")
async def api_backtest(req: BacktestRequest):
    try:
        import pandas as pd
        import io
        from contextlib import redirect_stdout
        import sys

        df = pd.DataFrame(req.data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        strategy_map = {
            "DailyT0Strategy": DailyT0Strategy,
            "GridT0Strategy": GridT0Strategy,
            "VolatilityT0Strategy": VolatilityT0Strategy,
            "EnhancedT0Strategy": EnhancedT0Strategy,
            "GridT0StrategyAdvanced": GridT0StrategyAdvanced,
            "TrendT0Strategy": TrendT0Strategy,
        }
        strategy = strategy_map.get(req.strategy, EnhancedT0Strategy)

        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        results = run_backtest(strategy, df, initial_cash=req.cash, commission=0.001)
        output = captured.getvalue()
        sys.stdout = old_stdout

        final_value = results[0].broker.getvalue()
        profit = final_value - req.cash
        profit_pct = profit / req.cash * 100

        return {
            "success": True,
            "log": output,
            "final_value": final_value,
            "profit": profit,
            "profit_pct": profit_pct
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/backtest_batch")
async def api_backtest_batch(req: BacktestBatchRequest):
    """接受多个回测任务并发执行。每个 job: {symbol, source, period, cash, strategy}"""
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _process(job):
            try:
                job_dict = dict(job)
                key = hashlib.sha256(json.dumps(job_dict, sort_keys=True).encode()).hexdigest()
                with _BACKTEST_CACHE_LOCK:
                    cached = _BACKTEST_CACHE.get(key)
                    if cached and time() - cached["ts"] < _CACHE_TTL:
                        logger.info(f"backtest cache hit {job_dict.get('symbol')}")
                        return {"success": True, "symbol": job_dict.get("symbol"), **cached["res"]}

                qp = QuantPlus(job_dict.get("source", "baostock"))
                if job_dict.get("period", "daily") == "daily":
                    df = qp.fetch(job_dict["symbol"])
                else:
                    df = qp.fetch_minute(job_dict["symbol"], period=job_dict.get("period", "5"), days=30)

                if df is None or len(df) == 0:
                    return {"success": False, "symbol": job_dict.get("symbol"), "error": "未获取到数据"}

                import pandas as pd
                import io
                import sys

                strategy_map = {
                    "DailyT0Strategy": DailyT0Strategy,
                    "GridT0Strategy": GridT0Strategy,
                    "VolatilityT0Strategy": VolatilityT0Strategy,
                    "EnhancedT0Strategy": EnhancedT0Strategy,
                    "GridT0StrategyAdvanced": GridT0StrategyAdvanced,
                    "TrendT0Strategy": TrendT0Strategy,
                }
                strategy = strategy_map.get(job_dict.get("strategy"), EnhancedT0Strategy)

                old_stdout = sys.stdout
                sys.stdout = captured = io.StringIO()
                results = run_backtest(strategy, df, initial_cash=job_dict.get("cash", 20000), commission=0.001)
                output = captured.getvalue()
                sys.stdout = old_stdout

                final_value = results[0].broker.getvalue()
                profit = final_value - job_dict.get("cash", 20000)
                profit_pct = profit / job_dict.get("cash", 20000) * 100

                res = {"log": output, "final_value": final_value, "profit": profit, "profit_pct": profit_pct}
                with _BACKTEST_CACHE_LOCK:
                    _BACKTEST_CACHE[key] = {"ts": time(), "res": res}

                return {"success": True, "symbol": job_dict.get("symbol"), **res}
            except Exception as e:
                return {"success": False, "symbol": job.get("symbol"), "error": str(e)}

        jobs = req.jobs if isinstance(req.jobs, list) else []
        results = []
        max_workers = max(1, min(MAX_BACKTEST_WORKERS, len(jobs)))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_process, j): j for j in jobs}
            for fut in as_completed(futures):
                results.append(fut.result())

        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)