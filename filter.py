
from .helpers import getDateDelta, isWeekend, save
import json
from json.decoder import JSONDecodeError
import math
from .model import TaskModel
from .reposition import Reposition


def Filter(
    newtasks,
    oldtasks,
    man_reschedule,
    reschedule_range,
    local_date,
    week_day_work,
):

    newtasks = newtasks
    oldtasks = oldtasks

    to_reschedule = {}
    newtask_range = {}

    # produce the limits of the range of new tasks, according to the model
    # limits ie, first and last date that has this task as a tuple
    if newtasks:
        for model in newtasks.values():
            newtask_range[model.id] = (
                math.floor(model.start_day),
                model.due_date - 1,
            )
    if man_reschedule:
        newtask_range.update(reschedule_range)

    # produce the limits of the range of old tasks, according to the record
    oldtask_range = {
        task_id: tuple([task_info[2][0], task_info[2][1] - 1])
        for task_id, task_info in oldtasks.items()
    }

    # TODO remove dis
    to_reschedule = {
        task_id: task_info[4] for task_id, task_info in oldtasks.items()
    }

    # combine the two dictionaries with limits
    task_range = dict(oldtask_range, **newtask_range)

    # invert this dictionary
    # to make the limits the key and the task(s) that have this limit
    # the values in a list
    inverted_tasks = {}

    for task_id, range in task_range.items():
        inverted_tasks[range] = inverted_tasks.get(range, []) + [task_id]

    # unique ranges (limits) of the tasks
    unique_ranges = list(inverted_tasks.keys())

    # union of these limits have to be found to group tasks that overlap
    # and that can affect each other
    union_ranges = []
    grouped_tasks = []
    # each list of tasks inside grouped_tasks would belong within the limits
    # present in union_ranges under same index

    # getting the union of the limits from unique_ranges and getting the
    # respective tasks into the above lists
    for begin, end in sorted(unique_ranges):
        # -1 to add task-group adjacent
        if union_ranges and union_ranges[-1][1] >= begin - 1:
            index = union_ranges.index(union_ranges[-1])

            grouped_tasks[index] = grouped_tasks[index] + inverted_tasks.get(
                (begin, end)
            )

            union_ranges[-1][1] = max(union_ranges[-1][1], end)
        else:
            union_ranges.append([begin, end])
            grouped_tasks.append(inverted_tasks.get((begin, end)))

    # lists are converted to tuples so they are hashable
    union_ranges = [(k, w) for k, w in union_ranges]

    # producing a dictionary from both the lists
    union_range_tasks = dict(zip(union_ranges, grouped_tasks))

    # save(newtasks)
    used_ranges = []

    # adding old tasks under the union of the limits of the new tasks into
    # the list that is considered for reposition
    for range, tasks in union_range_tasks.items():
        for t in tasks:
            # if the group contain a new task
            if t in newtask_range.keys():
                if range not in used_ranges:
                    used_ranges.append(range)
                # add all the other tasks in that group to
                for n in tasks:
                    if n not in newtask_range.keys():
                        # if n in to_reschedule.keys():
                        #     to_reschedule.pop(n)

                        # makes a lot of sense
                        # to prevent activation of old/retired tasks
                        if oldtasks[n][2][1] - oldtasks[n][2][0] > 0:
                            due_date = oldtasks[n][2][1]
                            hours_work = oldtasks[n][0]
                            gradient = oldtasks[n][1]
                            # modified_date = oldtasks[n][4]
                            # TODO just recheck why this is needed
                            id = str(n.strip("t"))

                            task = TaskModel(
                                id=id,
                                due=due_date,
                                work=hours_work,
                                week_day_work=week_day_work,
                                days=0,
                                gradient=gradient,
                                today=getDateDelta(local_date) + 1,
                            )
                            newtasks[(n, "", due_date)] = task
    newtasks = dict(sorted(newtasks.items(), key=lambda x: x[0][0]))

    return newtasks, used_ranges


# function to produce old schedules to be used for precedence in scheduling

# produce old schedule according to the day ranges given


def set_old_schedule(
    oldschedule,
    day_ranges,
    week_day_work,
    week_end_work,
    max_week_day_work,
    max_week_end_work,
    extrahours,
):
    days = []


    # expand out the days that are present in each range
    for dayrange in day_ranges:
        for day in range(dayrange[0], dayrange[1] + 1):
            days.append(day)


    # modify old schedule, remove unwanted days, change to dayDelta number,
    # set difference and sum
    for day, data in dict(oldschedule).items():
        dayDelta = getDateDelta(day)

        if dayDelta not in days:
            oldschedule[dayDelta] = oldschedule.pop(day)
        else:
            oldschedule.pop(day)
            continue

        sum_of_tasks = sum(data["quots"].values())
        # difference = 0
        if isWeekend(day):
            if week_end_work - sum_of_tasks > 0:
                difference = week_end_work - sum_of_tasks
            else:
                difference = (
                    max_week_end_work + extrahours.get(day, 0) - sum_of_tasks
                )
        else:
            if week_day_work - sum_of_tasks > 0:
                difference = week_day_work - sum_of_tasks
            else:
                difference = (
                    max_week_day_work + extrahours.get(day, 0) - sum_of_tasks
                )

        oldschedule[dayDelta]["data"] = {
            "difference": difference,
            "sum": sum_of_tasks,
        }






    # oldschedule.update(self.schedule)
    # self.schedule = oldschedule





    return oldschedule
    # self.schedule = schedule
