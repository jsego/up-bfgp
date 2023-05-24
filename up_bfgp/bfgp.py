import os
import random
import shutil
import subprocess
import tempfile
from typing import Optional, Callable, IO, List
from unified_planning.engines.results import PlanGenerationResultStatus
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.model import ProblemKind
from unified_planning.engines import PDDLPlanner, LogMessage
import sys
from unified_planning.io import PDDLReader


class BestFirstGeneralizedPlanner(PDDLPlanner):
    """ BFGP++ is a Generalized PDDLPlanner, which in turn is an Engine & OneshotPlanner """

    def __init__(self, **options):
        # Read known user-options and store them for using in the `solve` method
        super().__init__(self)
        self.credits = {
            "name": "BFGP++",
            "author": "Javier Segovia-Aguas, Sergio Jiménez, Anders Jonsson and collaborators",
            "contact": "javier.segovia@upf.edu (for UP integration)",
            "website": "bfgp_pp website",
            "license": "GPLv3",
            "short_description": "A framework based on BFGP where solutions are either assembly-like programs, or "
                                 "structured programs that are syntactically terminating.",
            "long_description": "A framework based on Best-First Generalized Planning where solutions are either "
                                "assembly-like programs, or structured programs that are syntactically terminating.",
        }
        self._mode = options.get('mode', 'synthesis')
        self._theory = options.get('theory', 'cpp')
        self._program_lines = options.get('program_lines', None)
        self._problem_folder = options.get('problem_folder', '..')
        self._evaluation_functions = options.get('evaluation_functions', None)

    @property
    def name(self) -> str:
        return self.credits['name']

    @staticmethod
    def supported_kind():
        """See unified_planning.model.problem_kind.py for more options """
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        return supported_kind

    @staticmethod
    def supports(problem_kind) -> bool:
        return problem_kind <= BestFirstGeneralizedPlanner.supported_kind()

    @staticmethod
    def preprocess(domain_filename: str, problem_filename: str) -> str:
        dest_dir = "tmp/"
        shutil.rmtree(dest_dir, ignore_errors=True)
        os.makedirs(dest_dir)
        cmd = f"python bfgp_pp/preprocess/pddl_translator.py " \
              f"-d {domain_filename} " \
              f"-i {problem_filename} " \
              f"-o {dest_dir} " \
              f"-id 1"
        subprocess.run(cmd.split())
        return dest_dir

    def _get_cmd(self, domain_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        compiled_folder = self.preprocess(domain_filename=domain_filename, problem_filename=problem_filename)
        return f"bfgp_pp/main.bin -m synthesis -t cpp -l 15 -f {compiled_folder} -o {plan_filename}".split()

    def _result_status(self,
                       problem: "up.model.Problem",
                       plan: Optional["up.plans.Plan"],
                       retval: int,
                       log_messages: Optional[List[LogMessage]] = None) \
            -> "up.engines.results.PlanGenerationResultStatus":
        """ Validate the problem """
        if retval != 0:
            return PlanGenerationResultStatus.INTERNAL_ERROR
        elif plan is None:
            return PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        else:
            return PlanGenerationResultStatus.SOLVED_SATISFICING



# Register the solver
env = up.environment.get_environment()
env.factory.add_engine('bfgp', __name__, 'BestFirstGeneralizedPlanner')

# Invoke planner
with env.factory.OneshotPlanner(name='bfgp') as p:
    reader = PDDLReader()
    pddl_problem = reader.parse_problem('bfgp_pp/domains/gripper/domain.pddl', 'bfgp_pp/domains/gripper/p01.pddl')
    print(pddl_problem)
    result = p.solve(pddl_problem, output_stream=sys.stdout)
    if result.status == PlanGenerationResultStatus.SOLVED_SATISFICING:
        print(f'{p.name} found a valid plan!')
        print(f'The plan is: {result.plan}')
        print('\n'.join(str(x) for x in result.plan.actions))
    else:
        print('No plan found!')
