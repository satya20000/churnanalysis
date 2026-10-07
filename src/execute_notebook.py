"""Execute notebook cells in a fresh Python process through IPython.

The hosted environment blocks socket binds required by Jupyter kernels. This
runner captures real stdout and display MIME bundles; it does not inject results.
Normal Jupyter/nbclient execution works on an unrestricted workstation.
"""
import contextlib,io,base64
from pathlib import Path
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.displaypub import DisplayPublisher
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
def execute():
    path=ROOT/'notebooks/01_saas_churn_analysis.ipynb'
    nb=nbformat.read(path,as_version=4);shell=InteractiveShell.instance()
    outputs=[]
    class Publisher(DisplayPublisher):
        def publish(self,data,metadata=None,**kwargs):
            outputs.append(nbformat.v4.new_output('display_data',data=data,metadata=metadata or {}))
    shell.display_pub=Publisher(parent=shell)
    def show(*args,**kwargs):
        for n in plt.get_fignums():
            fig=plt.figure(n);buf=io.BytesIO();fig.savefig(buf,format='png',bbox_inches='tight')
            outputs.append(nbformat.v4.new_output('display_data',data={'image/png':base64.b64encode(buf.getvalue()).decode(),'text/plain':'<Matplotlib figure>'},metadata={}))
        plt.close('all')
    plt.show=show
    count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1;outputs=[];stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stdout):
            result=shell.run_cell(cell.source,store_history=True)
        if result.error_in_exec or result.error_before_exec:
            raise RuntimeError(f'Cell {count} failed: {result.error_in_exec or result.error_before_exec}')
        if stdout.getvalue():outputs.insert(0,nbformat.v4.new_output('stream',name='stdout',text=stdout.getvalue()))
        cell.execution_count=count;cell.outputs=outputs
    nb.metadata['execution']={'method':'fresh-process IPython; socket-free display capture','reason':'Hosted runtime disallows TCP/IPC socket binds','code_cells_executed':count}
    nbformat.validate(nb);nbformat.write(nb,path)
    print(f'Executed {count} notebook code cells; saved real outputs.')
if __name__=='__main__':execute()
