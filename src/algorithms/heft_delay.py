from algorithms.algo_base import AlgoBase
from functools import cmp_to_key
from algorithms.heft import calculate_priority, find_processor
from platforms.memory import Memory
from platforms.task import Task


class HEFTDelay(AlgoBase):

    def schedule(self, tasks: list[Task], input, options: dict) -> tuple[list[list[Task]], int]:
        # print('delay version')
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        calculate_priority(entry_task)

        def task_compare(task1: Task, task2: Task):
            return task2.priority - task1.priority
        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))
        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]

        for task in sorted_tasks:
            est, eft, pid = find_processor(task, schedule)
            latest_start = est  # AST

            # allocate input tensor
            if task is entry_task:
                _, slot = self.memory.fit(input, [est, eft], task)
                if slot:
                    latest_start = max(latest_start, slot.interval[0])
            # allocate output tensor
            ok, slot = self.memory.fit(task.output, [
                est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
            if not ok:
                raise ValueError('Fail to allocate memory')
            if slot:
                latest_start = max(latest_start, slot.interval[0])

            ok, slot = self.memory.fit(
                task.buffer_size, [latest_start, latest_start + eft - est], task)
            if not ok:
                raise ValueError('Fail to allocate memory')
            if slot:
                latest_start = max(latest_start, slot.interval[0])

            ast = latest_start
            aft = latest_start + eft - est

            # free input tensors
            if task is not entry_task:
                # check if inputs can be free
                for in_edge in task.in_edges:
                    last_use = True
                    until = -1
                    for out_edge in in_edge.source.out_edges:
                        if out_edge.target is task:
                            continue
                        if out_edge.target.procId is None:  # not allocate yet
                            last_use = False
                            break
                        until = max(until, out_edge.target.aft)
                    if last_use:
                        until = max(until, aft)
                        self.memory.free_tensor(in_edge.source, until)

            # append task to schedule
            task.procId = pid + 1
            task.ast = ast
            task.aft = aft
            schedule[pid].append(task)
            # update makespan
            if task.aft > makespan:
                makespan = task.aft

        if options.get('plot', True):
            self.memory.plot(makespan, filename='heft-delay')
            self.plot(schedule, makespan, 'heft-delay')
        return schedule, makespan, self.memory.max()