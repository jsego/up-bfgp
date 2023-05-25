import os
import shutil
import subprocess
from typing import Optional, Callable, List, Union
from unified_planning.engines.results import PlanGenerationResultStatus
import unified_planning as up
from unified_planning.model import ProblemKind
from unified_planning.engines import PDDLPlanner, LogMessage
import sys
from unified_planning.io import PDDLReader
from unified_planning.plans.sequential_plan import SequentialPlan


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
        self.set_arguments(**options)

    def set_arguments(self, **options):
        self._mode = options.get('mode', 'synthesis')
        self._theory = options.get('theory', 'cpp')
        self._program_lines = options.get('program_lines', 10)
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
        # print(compiled_folder)
        command = f"bfgp_pp/main.bin -m {self._mode} -t {self._theory} -l {self._program_lines} " \
                  f"-f {compiled_folder} -o {plan_filename}".split()
        # print(command)
        return command

    def _plan_from_file(
        self,
        problem: "up.model.Problem",
        plan_filename: str,
        get_item_named: Callable[
            [str],
            Union[
                "up.model.Type",
                "up.model.Action",
                "up.model.Fluent",
                "up.model.Object",
                "up.model.Parameter",
                "up.model.Variable",
            ],
        ],
    ) -> "up.plans.Plan":
        # Validate the GP plan over the input problem
        dest_prog = f'tmp/gp_plan.prog'
        subprocess.run(f'cp {plan_filename} {dest_prog}', shell=True)
        command = f"bfgp_pp/main.bin -m validation-prog -t {self._theory} -f tmp/ -p {dest_prog}".split()
        subprocess.run(command)

        # Building candidate plan (from root folder)
        plan_file = "plan.1"
        plan = up.plans.SequentialPlan([])
        with open(plan_file) as pf:
            for line in pf:
                if line[0] == ';':
                    continue
                # Extract action and params data
                grounded_act = line[1:-2].split()
                action = get_item_named(grounded_act[0])
                params = [get_item_named(param) for param in grounded_act[1:]]
                # Build an ActionInstance with previous data
                plan.actions.append(up.plans.ActionInstance(action=action, params=params))

        # The validation starts
        assert problem.environment.factory.PlanValidator(name='sequential_plan_validator').validate(problem, plan)

        # Return the plan
        return plan


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
with env.factory.OneshotPlanner(name='bfgp') as bfgp:
    bfgp.set_arguments(program_lines=15)
    reader = PDDLReader()
    pddl_problem = reader.parse_problem('bfgp_pp/domains/gripper/domain.pddl', 'bfgp_pp/domains/gripper/p01.pddl')
    # print(pddl_problem)
    result = bfgp.solve(pddl_problem, output_stream=sys.stdout)
    if result.status == PlanGenerationResultStatus.SOLVED_SATISFICING:
        print(f'{bfgp.name} found a valid plan!')
        print(f'The plan is:')
        print('\n'.join(str(x) for x in result.plan.actions))
    else:
        print('No plan found!')
