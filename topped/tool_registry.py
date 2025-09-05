import os
import subprocess
from acpype.acs_api import acpype_api
from openff.toolkit import Molecule, Topology, ForceField
from openff.interchange import Interchange
from . import MATCHPATH

def wrap_match(inpath, outpath, tag, options={}):
    base_options = {"forcefield": "top_all36_cgenff_new"}
    base_options.update(options)
    try:
        subprocess.run([MATCHPATH, "-forcefield", base_options["forcefield"], inpath])
    except Exception as err:
        msg = "Excution of MATCH faild due to the following error."
        raise RuntimeError(msg) from err
    convert_charmm_to_gmx(outpath)

def wrap_acpype(inpath, outpath, tag, options={}):
    base_options = ["-i", str(inpath), 
                    "-c", options.get("c", "bcc"),
                    "-a", options.get("a", "gaff2"),
                    "-b", str(tag),
                    "-m", options.get("m", "1"),
                    "-n", options.get("c", "0")]
    try:
        cli = ["acpype"]+base_options
        # the API does not run correctly unfortunetly so we execute
        # it from the CLI
        subprocess.run(cli)
    except Exception as err:
        msg = "Excution of Acpype faild due to the following error."
        print(msg)
        print(err)
        #raise RuntimeError(msg) from err

def wrap_openff(inpath, outpath, tag, options={}):
    try:
        base_options = {"forcefield": "openff-2.0.0.offxml"}
        base_options.update(options)
        polymer = Molecule.from_file(inpath, file_format='sdf')
        topology = Topology.from_molecules([polymer])
        force_field = ForceField("openff-2.0.0.offxml")  # Let's stick to this one, although version 2.1.0 is also available
        interchange = Interchange.from_smirnoff(force_field, topology)
        openmm_system = interchange.to_openmm()
        openmm_topology = interchange.to_openmm_topology()
        openmm_positions = interchange.positions.to_openmm()
        # Output GROMACS files
        gromacs_filename_base = f'{outpath}/open_ff_polymer'
        interchange.to_gromacs(gromacs_filename_base)
    except Exception as err:
        print(err)
    
def wrap_ligpargen(inpath, outpath, tag, options={}):
    base_options = {"molname": "MOL",
                    "resname": "MOL",
                    "charge": 0,
                    "num_opts": 3,
                    "charge_method": "CM1A"}
    base_options.update(options)
    try:
        subprocess.run(["ligpargen", "-i", inpath, "-n", base_options["molname"],
                        "-p", outpath, "-r", base_options["resname"], 
                        "-c", base_options["charge"], "-o", base_options["num_opts"],
                        "-cgen", base_options["charge_method"]])
    except Exception as err:
        msg = "Excution of LigParGen faild due to the following error."
        raise RuntimeError(msg) from err

def wrap_grappa_amber(inpath, outpath, tag, options={}, run_acpype=True):
    if run_acpype:
        wrap_acpype(inpath, outpath, tag, options)
        inpath = f"{tag}.acpype/{tag}_GMX.top"
    # !grappa_gmx -t grappa-1.4.0 -f topol.top -o topol_grappa.top -p
    base_options = {"forcefield": "grappa-1.4.0"}
    base_options.update(options)
    try:
        subprocess.run(["grappa_gmx", "-t", base_options["forcefield"], "-f", inpath, "-o", f"{outpath}/grappa.top"])
    except Exception as err:
        msg = "Excution of GRAPPA faild due to the following error."
        raise RuntimeError(msg) from err


TOOL_REGISTRY = {"charmm36": wrap_match,
                 "gaff2": wrap_acpype,
                 "opls": wrap_ligpargen,
                 "grappa": wrap_grappa_amber, 
                 "openff": wrap_openff}
