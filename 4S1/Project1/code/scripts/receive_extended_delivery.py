"""Receive completed evidence and build presentation. No local model/evaluation."""
import datetime,json,subprocess,sys,tarfile,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CODE=ROOT/'code';STATIC=CODE/'webapp/static';KEY='C:/Users/User/.ssh/lisa_cenara70hx';HOST='osta@100.69.21.71';REMOTE='/home/osta/lisa-eval/code'
def run(args): return subprocess.check_output(args,text=True,encoding='utf-8',errors='replace')
def status(value):
    value['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();tmp=STATIC/'extended-status.tmp';tmp.write_text(json.dumps(value),encoding='utf-8');tmp.replace(STATIC/'extended-status.json')
try:
    while True:
        data=json.loads(run(['ssh','-i',KEY,'-o','BatchMode=yes',HOST,f'/home/osta/blip2-qformer-eval/.venv/bin/python {REMOTE}/scripts/extended_progress.py']))
        status(dict(data,state='running' if data['runner_active'] or data['finalizer_active'] else 'attention'))
        if data['ready']:break
        if not data['runner_active'] and not data['finalizer_active']:raise RuntimeError('Remote run stopped before delivery completed')
        time.sleep(55)
    for name,destination in [('extended_public_20260915.tar.gz',STATIC),('extended_records_20260915.tar.gz',CODE)]:
        archive=CODE/'results'/name
        run(['scp','-O','-i',KEY,'-o','BatchMode=yes',f'{HOST}:{REMOTE}/results/{name}',str(archive)])
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                assert (destination/member.name).resolve().is_relative_to(destination.resolve())
                assert not member.issym() and not member.islnk()
            tar.extractall(destination)
    for script in ['build_extended_report.py','build_research_portal.py','validate_research_portal.py']:
        print(run([str(CODE/'.venv311/Scripts/python.exe'),str(CODE/'scripts'/script)]),flush=True)
    status(dict(data,state='complete'))
    print('LOCAL_DELIVERY_COMPLETE',flush=True)
except Exception as error:
    status({'state':'attention','message':'Delivery requires inspection; completed historical results remain available.'})
    traceback.print_exc();sys.exit(1)
