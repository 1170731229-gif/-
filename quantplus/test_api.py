import requests, time, json, os

base = 'http://127.0.0.1:8000'
out_path = os.path.join(os.path.dirname(__file__), 'test_api_output_full.txt')

def log(msg, fh=None):
    line = str(msg)
    print(line)
    if fh:
        fh.write(line + '\n')

def wait_up(timeout=15):
    t0=time.time()
    while time.time()-t0 < timeout:
        try:
            r = requests.get(base + '/docs', timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(0.5)
    return False

with open(out_path, 'a', encoding='utf-8') as fh:
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    fh.write('\n=== Test run: {} ===\n'.format(ts))
    log('waiting for server...', fh)
    if not wait_up(20):
        log('server not up', fh)
        raise SystemExit(1)

    log('calling /api/recommend', fh)
    try:
        r = requests.post(base + '/api/recommend', json={'count':6,'market':'all'}, timeout=20)
        log('recommend status ' + str(r.status_code), fh)
        log(r.text, fh)
    except Exception as e:
        log('recommend error ' + str(e), fh)

    log('\ncalling /api/backtest_batch', fh)
    try:
        payload = {'jobs':[{'symbol':'002475','source':'baostock','period':'daily','cash':20000,'strategy':'EnhancedT0Strategy'}]}
        r = requests.post(base + '/api/backtest_batch', json=payload, timeout=120)
        log('backtest_batch status ' + str(r.status_code), fh)
        log(r.text, fh)
    except Exception as e:
        log('backtest_batch error ' + str(e), fh)

    fh.write('=== End run ===\n')
