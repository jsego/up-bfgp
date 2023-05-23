import random
from typing import Optional, Callable, IO
from unified_planning.engines.results import PlanGenerationResultStatus
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.model import ProblemKind

class MySolverImpl(engines.Engine,
                   engines.mixins.OneshotPlannerMixin):
    def __init__(self, **options):
        # Read known user-options and store them for using in the `solve` method
        engines.Engine.__init__(self)
        engines.mixins.OneshotPlannerMixin.__init__(self)
        self.max_tries = options.get('max_tries', None)
        self.restart_probability = options.get('restart_probability', 0.00001)

    @property
    def name(self) -> str:
        return "YOLOPlanner"

    @staticmethod
    def supported_kind():
        # For this demo we limit ourselves to numeric planning.
        # Other kinds of problems can be modeled in the UP library,
        # see unified_planning.model.problem_kind.
        supported_kind = ProblemKind()
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_typing('HIERARCHICAL_TYPING')
        supported_kind.set_numbers('CONTINUOUS_NUMBERS')
        supported_kind.set_numbers('DISCRETE_NUMBERS')
        supported_kind.set_fluents_type('NUMERIC_FLUENTS')
        supported_kind.set_fluents_type('OBJECT_FLUENTS')
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS')
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS')
        supported_kind.set_conditions_kind('EQUALITIES')
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS')
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS')
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS')
        supported_kind.set_effects_kind('INCREASE_EFFECTS')
        supported_kind.set_effects_kind('DECREASE_EFFECTS')
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= MySolverImpl.supported_kind()

    def _solve(self, problem: 'up.model.Problem',
              callback: Optional[Callable[['up.engines.PlanGenerationResult'], None]] = None,
              timeout: Optional[float] = None,
              output_stream: Optional[IO[str]] = None) -> 'up.engines.results.PlanGenerationResult':
        env = problem.environment

        # First we ground the problem
        with env.factory.Compiler(problem_kind=problem.kind, compilation_kind=engines.CompilationKind.GROUNDING) as grounder:
            grounding_result = grounder.compile(problem, engines.CompilationKind.GROUNDING)
        grounded_problem = grounding_result.problem
        
        # We store the grounded actions in a list
        actions = list(grounded_problem.instantaneous_actions)
        
        # The candidate plan, initially empty
        plan = up.plans.SequentialPlan([])

        # Ask for an instance of a PlanValidator by name
        # (`sequential_plan_validator` is a python implementation of the 
        # PlanValidator operation mode offered by the UP library)
        with env.factory.PlanValidator(name='sequential_plan_validator') as pv:
            counter = 0
            while True:
                # With a certain probability, restart from scratch to avoid dead-ends
                if random.random() < self.restart_probability:
                    plan = up.plans.SequentialPlan()
                else:
                    # Select a random action
                    a = random.choice(actions)
                    # Create the relative action instance
                    ai = up.plans.ActionInstance(a)
                    # Append the action to the plan
                    plan.actions.append(ai)

                    # Check plan validity
                    res = pv.validate(grounded_problem, plan)
                    if res:
                        # If the plan is valid, lift the action instances and
                        # return the resulting plan
                        resplan = plan.replace_action_instances(grounding_result.map_back_action_instance)
                        # Sanity check
                        assert pv.validate(problem, resplan)
                        return up.engines.PlanGenerationResult(PlanGenerationResultStatus.SOLVED_SATISFICING, resplan, self.name)
                    else:
                        # If the plan is invalid, check if the reason is action
                        # applicability (as opposed to goal satisfaction)
                        einfo = res.log_messages[0].message
                        if 'Goals' not in einfo:
                            # If the plan is not executable, remove the last action
                            plan.actions.pop()
                    # Limit the number of tries, according to the user specification
                    counter += 1
                    if self.max_tries is not None and counter >= self.max_tries:
                        return up.engines.PlanGenerationResult(PlanGenerationResultStatus.TIMEOUT, None, self.name)

    def destroy(self):
        pass
        
        
# Register the solver
env = up.environment.get_environment()
env.factory.add_engine('yoloplanner', __name__, 'MySolverImpl')


# Domain and instance
emgr = env.expression_manager

Location = env.type_manager.UserType('Location')
robot_at = up.model.Fluent('robot_at', env.type_manager.BoolType(), loc=Location)
battery_charge = up.model.Fluent('battery_charge', env.type_manager.RealType(0, 100))
move = up.model.InstantaneousAction('move', l_from=Location, l_to=Location)
l_from = move.parameter('l_from')
l_to = move.parameter('l_to')
move.add_precondition(emgr.GE(battery_charge, 10))
move.add_precondition(emgr.Not(emgr.Equals(l_from, l_to)))
move.add_precondition(robot_at(l_from))
move.add_precondition(emgr.Not(robot_at(l_to)))
move.add_effect(robot_at(l_from), False)
move.add_effect(robot_at(l_to), True)
move.add_effect(battery_charge, emgr.Minus(battery_charge, 10))
l1 = up.model.Object('l1', Location)
l2 = up.model.Object('l2', Location)
problem = up.model.Problem('robot')
problem.add_fluent(robot_at)
problem.add_fluent(battery_charge)
problem.add_action(move)
problem.add_object(l1)
problem.add_object(l2)
problem.set_initial_value(robot_at(l1), True)
problem.set_initial_value(robot_at(l2), False)
problem.set_initial_value(battery_charge, 100)
problem.add_goal(robot_at(l2))


# Invoke planner
with env.factory.OneshotPlanner(name='yoloplanner') as p:
    result = p.solve(problem)
    if result.status == PlanGenerationResultStatus.SOLVED_SATISFICING:
        print(f'{p.name} found a valid plan!')
        print(f'The plan is: {result.plan}')
        print('\n'.join(str(x) for x in result.plan.actions))
    else:
        print('No plan found!')
