import random
from typing import Optional, Callable, IO, List
from unified_planning.engines.results import PlanGenerationResultStatus
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.model import ProblemKind
from unified_planning.engines import PDDLPlanner, LogMessage
import sys


class BestFirstGeneralizedPlannerPP(PDDLPlanner):
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
        self._problem_folder = options.get('problem_folder', '.')
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
        return problem_kind <= BestFirstGeneralizedPlannerPP.supported_kind()

    def _get_cmd(self, domain_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        print(plan_filename)
        return f"bfgp_pp/main.bin -m synthesis -t cpp -l 15 -f bfgp_pp/domains/synthesis/gripper/ -o {plan_filename}".split()



    def _result_status(self, problem: "up.model.Problem", plan: Optional["up.plans.Plan"], retval: int,
                       log_messages: Optional[
                           List[LogMessage]] = None) -> "up.engines.results.PlanGenerationResultStatus":
        """ Validate the problem """
        return up.engines.results.PlanGenerationResultStatus.SOLVED_SATISFICING



# Register the solver
env = up.environment.get_environment()
env.factory.add_engine('bfgp_pp', __name__, 'BestFirstGeneralizedPlannerPP')

# Domain and instance
emgr = env.expression_manager

Location = env.type_manager.UserType('Location')
robot_at = up.model.Fluent('robot_at', env.type_manager.BoolType(), loc=Location)
move = up.model.InstantaneousAction('move', l_from=Location, l_to=Location)
l_from = move.parameter('l_from')
l_to = move.parameter('l_to')
move.add_precondition(emgr.Not(emgr.Equals(l_from, l_to)))
move.add_precondition(robot_at(l_from))
move.add_precondition(emgr.Not(robot_at(l_to)))
move.add_effect(robot_at(l_from), False)
move.add_effect(robot_at(l_to), True)
l1 = up.model.Object('l1', Location)
l2 = up.model.Object('l2', Location)
problem = up.model.Problem('robot')
problem.add_fluent(robot_at)
problem.add_action(move)
problem.add_object(l1)
problem.add_object(l2)
problem.set_initial_value(robot_at(l1), True)
problem.set_initial_value(robot_at(l2), False)
problem.add_goal(robot_at(l2))

# Invoke planner
with env.factory.OneshotPlanner(name='bfgp_pp') as p:
    result = p.solve(problem, output_stream=sys.stdout)
    if result.status == PlanGenerationResultStatus.SOLVED_SATISFICING:
        print(f'{p.name} found a valid plan!')
        print(f'The plan is: {result.plan}')
        print('\n'.join(str(x) for x in result.plan.actions))
    else:
        print('No plan found!')
