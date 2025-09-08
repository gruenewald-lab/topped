import os
import subprocess
import shutil
import tempfile
import vermouth
from vermouth.pdb.pdb import write_pdb
from vermouth.gmx.gro import write_gro
from .tool_registry import TOOL_REGISTRY

COORD_WRITERS = {"pdb": write_pdb,
                 "gro": write_gro}

class TopolGenerator():

    def __init__(self,
                 toolname,
                 input_format="pdb",
                 tool_options={},
                 outpath=None,
                 ):
        self.toolname = toolname
        self.top_tool = TOOL_REGISTRY.get(toolname)
        if self.top_tool is None:
            msg = f"Tool with name {toolname} not found in registry."
            raise IOError(msg)
        self.input_format = input_format
        self.outpath = outpath
        self.tmppath = None
        self.tool_options = tool_options

    def prepare(self, molecule, molname):
        # make temporary directory
        dirname = f"{self.toolname}_{molname}"
        tmppath = tempfile.mkdtemp(dirname)
        pdb_dir = f"{tmppath}/input.pdb"
        # convert molecule to input format
        system = vermouth.System()
        system.molecules.append(molecule)
        COORD_WRITERS['pdb'](system, 
                             pdb_dir,
                             defer_writing=False)
        if self.input_format == 'sdf':
            subprocess.run(['obabel', '-i', 'pdb', str(pdb_dir), '-o', 'sdf', '-O', f"{tmppath}/{molname}.sdf"])
            pdb_dir = f"{tmppath}/{molname}.sdf"
            pdb_dir.write_text(f'{molname}\n' + '\n'.join(p.read_text().splitlines()[1:]))
        return tmppath, pdb_dir

    def post_process(self, tmppath):
        # clear the tmp dict       
        # If you have a tmpdir path
        current_dir = os.getcwd()
        # Move entire directory
        shutil.move(tmppath, current_dir)

    def run_molecule(self, molecule):
        cwd = os.getcwd()
        molname = molecule.molname
        tmppath, input_file = self.prepare(molecule, molname)
        os.chdir(tmppath)
        print(input_file)
        self.top_tool(input_file, tmppath, molname, self.tool_options)
        os.chdir(cwd)
        shutil.move(tmppath, cwd)
