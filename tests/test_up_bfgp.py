from unified_planning.shortcuts import *  # type: ignore
from unified_planning.io import PDDLReader
from collections import namedtuple  # type: ignore
from unified_planning.plans import PlanKind  # type: ignore
import unittest
from unified_planning.engines.results import PlanGenerationResultStatus
import up_bfgp

class BFGPtest(unittest.TestCase):
    def test_bfgp(self):
        """Testing the BFGP++ solvers can solve 3 different Gripper instances"""
        with OneshotPlanner(name='bfgp', params={'program_lines': 15}) as bfgp:
            reader = PDDLReader()
            pddl_problem = reader.parse_problem('./gripper/domain.pddl', './gripper/p01.pddl')
            result = bfgp.solve(pddl_problem)
            self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)
            pddl_problem = reader.parse_problem('./gripper/domain.pddl', './gripper/p02.pddl')
            result = bfgp.solve(pddl_problem)
            self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)
            pddl_problem = reader.parse_problem('./gripper/domain.pddl', './gripper/p03.pddl')
            result = bfgp.solve(pddl_problem)
            self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)
            print(f'{bfgp.name} found a valid plan for {pddl_problem.name}!')
            print(f'The plan is:')
            print('\n'.join(str(x) for x in result.plan.actions))


if __name__ == "__main__":
    unittest.main()