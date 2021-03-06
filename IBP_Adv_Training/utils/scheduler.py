# Copyright (C) 2020, Jiameng Fan <jmfan@bu.edu>
#
# This program is licenced under the MIT License,
# contained in the LICENCE file in this directory.


import numpy as np


class Scheduler():
    def __init__(
        self, schedule_type, init_step, final_step, init_value, final_value,
        num_steps_per_epoch, mid_point=.25, beta=4.
    ):
        self.schedule_type = schedule_type
        self.init_step = init_step
        self.final_step = final_step
        self.init_value = init_value
        self.final_value = final_value
        self.mid_point = mid_point
        self.beta = beta
        self.num_steps_per_epoch = num_steps_per_epoch
        assert self.final_step >= self.init_step
        assert self.beta >= 2.
        assert self.mid_point >= 0. and self.mid_point <= 1.

    def get_eps(self, epoch, step):
        if self.schedule_type == "smoothed":
            return self.smooth_schedule(
                epoch * self.num_steps_per_epoch + step, self.init_step,
                self.final_step, self.init_value, self.final_value,
                self.mid_point, self.beta
            )
        elif self.schedule_type == "linear":
            return self.linear_schedule(
                epoch * self.num_steps_per_epoch + step, self.init_step,
                self.final_step, self.init_value, self.final_value
            )
        elif self.schedule_type == "step":
            return self.step_schedule(
                epoch * self.num_steps_per_epoch + step, self.init_step,
                self.final_step, self.init_value, self.final_value
            )
        else:
            raise ValueError("Unknown type of scheduler")

    # Smooth schedule that slowly morphs into a linear schedule.
    # Code is adapted from DeepMind's IBP implementation:
    # https://github.com/deepmind/interval-bound-propagation/blob/2c1a56cb0497d6f34514044877a8507c22c1bd85/interval_bound_propagation/src/utils.py#L84
    def smooth_schedule(
        self, step, init_step, final_step, init_value,
        final_value, mid_point=.25, beta=4.
    ):
        """Smooth schedule that slowly morphs into a linear schedule."""
        try:
            assert final_value >= init_value
        except ValueError:
            assert (final_value >= init_value).all()
        assert final_step >= init_step
        assert beta >= 2.
        assert mid_point >= 0. and mid_point <= 1.
        mid_step = int((final_step - init_step) * mid_point) + init_step
        if mid_step <= init_step:
            alpha = 1.
        else:
            t = (mid_step - init_step) ** (beta - 1.)
            alpha = (final_value - init_value) / (
                (final_step - mid_step) * beta * t + (mid_step - init_step) * t
            )
        mid_value = alpha * (mid_step - init_step) ** beta + init_value
        is_ramp = float(step > init_step)
        is_linear = float(step >= mid_step)
        return (is_ramp * (
            (1. - is_linear) * (
                init_value +
                alpha * float(step - init_step) ** beta) +
            is_linear * self.linear_schedule(
                step, mid_step, final_step, mid_value, final_value)) +
                (1. - is_ramp) * init_value)

    # Linear schedule.
    # Code is adapted from DeepMind's IBP implementation:
    # https://github.com/deepmind/interval-bound-propagation/blob/2c1a56cb0497d6f34514044877a8507c22c1bd85/interval_bound_propagation/src/utils.py#L73
    def linear_schedule(
        self, step, init_step, final_step, init_value, final_value
    ):
        """Linear schedule."""
        assert final_step >= init_step
        try:
            if step < init_step and init_value > final_value:
                return init_value
        except ValueError:
            if step < init_step and (init_value > final_value).all():
                return init_value
        if init_step == final_step:
            return final_value
        rate = float(step - init_step) / float(final_step - init_step)
        linear_value = rate * (final_value - init_value) + init_value
        return np.clip(
            linear_value, np.minimum(init_value, final_value),
            np.maximum(init_value, final_value)
        )

    # Step scheduler: zero or final value after certain steps
    def step_schedule(
        self, step, init_step, final_step, init_value, final_value
    ):
        """step schedule"""
        assert final_step >= init_step
        if init_step == final_step:
            return final_value
        if step <= init_value:
            return init_value
        value = init_value if step <= final_step else final_value
        return value
