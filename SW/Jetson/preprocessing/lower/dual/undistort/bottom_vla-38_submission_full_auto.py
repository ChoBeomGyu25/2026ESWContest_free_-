import copy
import importlib.util
import math
import select
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
BUILD = '2026-09-02-bottom-vla-v38-submission-full-auto'

def _load_v23():
    candidates = [Path(__file__).resolve().parent / 'bottom_vla-23_submission_runtime.py', Path('/workspace/project_train/aruco_test/dual/undistort/bottom_vla-23_submission_runtime.py')]
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location('bottom_vla_v23_runtime', str(path))
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules['bottom_vla_v23_runtime'] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError('bottom_vla-23_submission_runtime.py not found beside bottom_vla-38_submission_full_auto.py or in the undistort directory')
v23 = _load_v23()
v23.BUILD = BUILD

class _D60FeedbackProxy:

    def __init__(self, delegate, app, module, real_arm, arm_key):
        object.__setattr__(self, '_delegate', delegate)
        object.__setattr__(self, '_app', app)
        object.__setattr__(self, '_module', module)
        object.__setattr__(self, '_real_arm', real_arm)
        object.__setattr__(self, '_arm_key', str(arm_key).upper())

    def __getattr__(self, name):
        return getattr(self._delegate, name)

    def __setattr__(self, name, value):
        if name in {'_delegate', '_app', '_module', '_real_arm', '_arm_key'}:
            object.__setattr__(self, name, value)
        else:
            setattr(self._delegate, name, value)

    def _feedback_rule(self, angle, stage):
        text = str(stage or '').upper()
        value = float(angle)
        if 'FINAL_DUAL_CLOSE' in text or value >= 3.2:
            return ('FINAL_CLOSE', 2.8, None)
        if 'LIMITED_CLOSE' in text or value >= 2.95:
            return ('CLOSE', 2.7, None)
        return None

    def set_gripper(self, angle_rad, *args, **kwargs):
        result = self._delegate.set_gripper(angle_rad, *args, **kwargs)
        rule = self._feedback_rule(angle_rad, kwargs.get('stage'))
        if rule is None:
            return result
        kind, minimum, maximum = rule
        last = None
        for attempt in range(1, 5):
            if attempt > 1:
                result = self._delegate.set_gripper(angle_rad, *args, **kwargs)
            time.sleep(0.18)
            actual = self._app._read_gripper_angle(self._module, self._real_arm)
            if actual is None:
                print(f'[D60-GRIP-V34] {self._arm_key} {kind} attempt={attempt}/4 feedback=NONE')
                continue
            last = float(actual)
            accepted = bool(last >= float(minimum)) if minimum is not None else bool(last <= float(maximum))
            limit_text = f'>={float(minimum):.2f}' if minimum is not None else f'<={float(maximum):.2f}'
            print(f'[D60-GRIP-V34] {self._arm_key} {kind} attempt={attempt}/4 cmd={float(angle_rad):.3f} actual={last:.3f} gate={limit_text} accepted={accepted}')
            if accepted:
                return result
        raise RuntimeError(f'D60 {self._arm_key} {kind} feedback gate failed cmd={float(angle_rad):.3f} actual={last}')

def _make_app_class(base, align_mod, front, source_paths):
    front.d60_waist_grip_body_min_mm = 12.0
    front.d60_waist_grip_body_max_mm = 60.0
    front.d60_waist_grip_tangent_max_mm = 45.0
    front.d60_waist_grip_endpoint_radius_max_mm = 80.0
    front.d60_pose_waist_min_width_mm = 80.0
    front.d60_pose_waist_max_width_mm = 470.0
    front.d60_waist_hard_max_width_mm = 9999.0
    front.basket_placement_extra_deg = 20.0
    front.basket_placement_lower_mm = 140.0
    Base = v23._make_app_class(base, align_mod, front, source_paths)

    class BottomVLAApp(Base):

        def __init__(self, args):
            self._auto_judge_lock = threading.RLock()
            self._v33_d60_rescue_lock = threading.RLock()
            self._auto_judge_busy = False
            self._v30_source_warning_signature = None
            self._v30_last_trusted_mask_area_px = None
            self._v30_fallback_min_ratio = 0.45
            super().__init__(args)
            self.bottom_vla_build = BUILD
            self.front.basket_placement_extra_deg = 20.0
            self.front.basket_placement_lower_mm = 140.0
            self.front.d60_waist_grip_body_min_mm = 12.0
            self.front.d60_waist_grip_body_max_mm = 60.0
            self.front.d60_waist_grip_tangent_max_mm = 45.0
            self.front.d60_waist_grip_endpoint_radius_max_mm = 80.0
            self.front.d60_pose_waist_min_width_mm = 80.0
            self.front.d60_pose_waist_max_width_mm = 470.0
            self.front.d60_waist_hard_max_width_mm = 9999.0
            self.d56_args.d31_grip_open = 1.35
            self.d56_args.step60_pullup_speed = 0.6
            self.d56_args.step67_outbound_edge_mm_s = 380.0
            self.d56_args.step67_outbound_deep_mm_s = 340.0
            self._v33_d54_old_arm2_inward = float(getattr(self.d54_args, 'd54_arm2_physical_inward_mm', 12.0))
            self._v33_d54_old_arm1_inward = float(getattr(self.d54_args, 'd54_arm1_physical_inward_mm', 5.0))
            self._v33_d54_old_target_depth = float(getattr(self.d54_args, 'd54_physical_target_depth_mm', 22.0))
            self.d54_args.d54_arm2_physical_inward_mm = max(self._v33_d54_old_arm2_inward, 35.0)
            self.d54_args.d54_arm1_physical_inward_mm = max(self._v33_d54_old_arm1_inward, 35.0)
            self.d54_args.d54_physical_target_depth_mm = max(self._v33_d54_old_target_depth, 32.0)
            self.d55_args.d55v11_xy_guard_radius_mm = 10.0
            self.d55_args.d55v11_xy_guard_min_ratio = 0.85
            self.d55_args.d55v11_xy_guard_max_inward_mm = 60.0
            self.d55_args.d55v14_mask_core_inset_mm = 25.0
            self._v30_d58_arm1_z_offset_mm = -10.0
            self._v30_align_surface_z_offset_mm = -8.0
            self._v30_align_line_done_mm = 22.0
            self._v30_align_angle_done_deg = 5.0
            self._v30_align_move_min_mm = 35.0
            self._v30_align_move_max_mm = 155.0
            self._install_full_board_mask_roi()
            self._install_d58_arm1_contact_z_offset()
            self._install_align_surface_z_offset()
            self._install_align_centerline_policy()
            d55_arm2_base = getattr(self.d55_args, 'arm2_press_z', None)
            if d55_arm2_base is None:
                d55_arm2_base = getattr(self.d55_args, 'press_z', None)
            if d55_arm2_base is not None:
                self.d55_args.arm2_press_z = float(d55_arm2_base) - 5.0
            print(f'[BOTTOM-VLA] build={BUILD}')
            print('[BASKET-V33] placement extra rotation=20.0deg; final closed descent 180->140mm, then release')
            print('[BASKET-V33-CLOSE] CLOSE-VERIFY accepts feedback >=2.80rad, then preserves final 3.32rad + T107=1000 latch')
            print('[BASKET-V33-STANDBY] ARM2 standby T104 is re-sent up to 4 times if feedback does not reach standby')
            print('[D60-V33-SPEED] outbound EDGE=380mm/s DEEP=340mm/s; pull-up speed=0.60')
            print('[PERCEPTION-V33] small CRUMPLED/BGDIFF fallback under 45% of last trusted mask gets one fresh retry, then execution is blocked if still undersized')
            print('[SOURCE-V33] on-disk source hash changes warn but do not brick the already-loaded runtime')
            print('[AUTO-JUDGE] fresh current-state semantic selection preserved')
            print('[D60-V33] strict v21 waist gate remains first: body=12..60mm tangent<=45mm radius<=80mm poseWidth=80..470mm')
            print('[D60-V33-RESCUE] only zero-pair candidate failures retry geometry=8..82mm tangent<=65mm radius<=110mm, then 0/35mm soft workspace overlap; actual motion planner must still pass')
            print('[D60-V34-GRIP] pre-contact OPEN restored to 1.35rad and is never T105-retried; CLOSE 3.05 / FINAL 3.32 keep feedback verification')
            print(f'[D54-V33-INSET] adaptive physical inward cap A2={self._v33_d54_old_arm2_inward:.1f}->{float(self.d54_args.d54_arm2_physical_inward_mm):.1f}mm A1={self._v33_d54_old_arm1_inward:.1f}->{float(self.d54_args.d54_arm1_physical_inward_mm):.1f}mm targetDepth={self._v33_d54_old_target_depth:.1f}->{float(self.d54_args.d54_physical_target_depth_mm):.1f}mm')
            print('[D55-V33-MASK-GUARD] contact support radius=10mm ratio>=0.85 mask-core>=25mm; inward correction<=60mm while preserving sweep vector and Z')
            print('[D58-V33] ARM1 effective contact/mid/sweep surface Z offset=-10.0mm')
            print('[MASK-V33] perception/planning board shrink and D35 ROI inset forced to 0px; strict ArUco board clipping preserved; D60 35mm grasp-safe inset unchanged')
            print('[ALIGN-V34] old dual-waist Y recenter disabled; fresh waist-center to crotch/lower-center vector is the ALIGN authority')
            print('[ALIGN-V34] near-parallel WAIST correction uses the full remaining midpoint-to-white-line distance instead of the native 95mm cap')
            print('[ALIGN-V34] exact translation is used only when angle<=5deg, endpoint disagreement<=30mm, same-side errors, and the ARM2 target stays safe')
            print('[ALIGN-V34] non-parallel native WAIST/THIGH correction and single-arm surface/contact offset=-8.0mm remain unchanged')
            print('[D55-V33] folded-leg geometry separates FOLD_BOUNDARY from normal wrinkles and enables FOLDED_LEG_RECOVERY')
            if d55_arm2_base is not None:
                print(f'[D55-V33] ARM2 press Z {float(d55_arm2_base):.1f}->{float(self.d55_args.arm2_press_z):.1f}mm preserved from v27; ARM1 unchanged')
            self._submission_cycle_lock = threading.RLock()
            self._submission_cycle_active = False
            self._submission_cycle_epoch = 0
            self._submission_dispatch_pending = False
            self._submission_last_dispatched_plan_id = None
            self._submission_reason_counts = {}
            self._submission_blocked_reason = ''
            self._submission_finished = False
            self._submission_auto_rejudge_limit = 2
            self._submission_consecutive_press = 0
            self._submission_press_repeat_limit = 2
            self._submission_force_position_after_basket = True
            self._submission_fold_leg_balance_threshold = 0.70
            self._submission_fold_hem_balance_threshold = 0.58
            self._submission_midvector_asym_threshold = 0.22
            self._submission_print_provenance()
            print(f'[AUTO-POLICY-V38] BASKET_GRASP is always followed by one forced POSITION_ADJUST; after that normal AUTO-JUDGE resumes')
            print(f'[AUTO-POLICY-V38] heavy fold + center-vector asymmetry triggers WAIST_PULL_LAYDOWN before PRESS_SWEEP: leg<{self._submission_fold_leg_balance_threshold:.2f} or hem<{self._submission_fold_hem_balance_threshold:.2f}, midAsym>={self._submission_midvector_asym_threshold:.2f}')
            print(f'[AUTO-POLICY-V38] PRESS_SWEEP consecutive limit={self._submission_press_repeat_limit}; after the limit, non-PRESS structural actions are evaluated first and no third consecutive PRESS is dispatched')

        def _gentle_arms(self, arms, module, approach_min, release_min, prefix):
            is_d60 = str(prefix).upper() == 'D60'
            effective_approach = 1.35 if is_d60 else approach_min
            wrapped = super()._gentle_arms(arms, module, effective_approach, release_min, prefix)
            if not is_d60:
                return wrapped
            out = {}
            for key, proxy in wrapped.items():
                real_arm = arms.get(key) if isinstance(arms, dict) else None
                if proxy is None or real_arm is None:
                    out[key] = proxy
                else:
                    out[key] = _D60FeedbackProxy(proxy, self, module, real_arm, key)
            return out

        def _v33_d60_rescue_limits(self):
            return {'body_min_mm': 8.0, 'body_max_mm': 82.0, 'tangent_max_mm': 65.0, 'radius_max_mm': 110.0}

        def _v33_d60_force_rescue_once(self, obs, source_plan, overlap_mm):
            limits = self._v33_d60_rescue_limits()
            with self._v33_d60_rescue_lock:
                old = (float(self.front.d60_waist_grip_body_min_mm), float(self.front.d60_waist_grip_body_max_mm), float(self.front.d60_waist_grip_tangent_max_mm), float(self.front.d60_waist_grip_endpoint_radius_max_mm), float(self.cfg56.center_dead_half_width))
                try:
                    self.front.d60_waist_grip_body_min_mm = float(limits['body_min_mm'])
                    self.front.d60_waist_grip_body_max_mm = float(limits['body_max_mm'])
                    self.front.d60_waist_grip_tangent_max_mm = float(limits['tangent_max_mm'])
                    self.front.d60_waist_grip_endpoint_radius_max_mm = float(limits['radius_max_mm'])
                    self.cfg56.center_dead_half_width = -abs(float(overlap_mm)) if float(overlap_mm) > 0.0 else 0.0
                    plan, motion, report = super()._d60_force_waist_endpoint_plan(obs, source_plan)
                finally:
                    self.front.d60_waist_grip_body_min_mm = old[0]
                    self.front.d60_waist_grip_body_max_mm = old[1]
                    self.front.d60_waist_grip_tangent_max_mm = old[2]
                    self.front.d60_waist_grip_endpoint_radius_max_mm = old[3]
                    self.cfg56.center_dead_half_width = old[4]
            if plan is not None and motion is not None:
                metrics = dict(getattr(plan, 'metrics', {}) or {})
                metrics['bottom_vla_v33_d60_rescue'] = True
                metrics['bottom_vla_v33_d60_rescue_overlap_mm'] = float(overlap_mm)
                metrics['bottom_vla_v33_d60_rescue_limits'] = dict(limits)
                plan.metrics = metrics
                report = dict(report or {})
                report['bottom_vla_v33_d60_rescue'] = True
                report['bottom_vla_v33_d60_rescue_overlap_mm'] = float(overlap_mm)
                report['bottom_vla_v33_d60_rescue_limits'] = dict(limits)
                print(f"[D60-V33-RESCUE-PASS] overlap={float(overlap_mm):.0f}mm pairTrials={int(report.get('pair_trials', 0) or 0)}")
            return (plan, motion, report)

        def _d60_force_waist_endpoint_plan(self, obs, source_plan):
            plan, motion, report = super()._d60_force_waist_endpoint_plan(obs, source_plan)
            if plan is not None and motion is not None:
                return (plan, motion, report)
            rep = dict(report or {})
            reason = str(rep.get('reason', ''))
            pair_trials = int(rep.get('pair_trials', 0) or 0)
            if reason != 'NO_KINEMATICALLY_SAFE_MASK_PAIR_BELOW_WAIST_ENDPOINTS' or pair_trials != 0:
                return (plan, motion, report)
            print('[D60-V33-RESCUE] strict planner had zero pair trials; retrying candidate gates before declaring unreachable')
            last = (plan, motion, report)
            for overlap_mm in (0.0, 35.0):
                candidate = self._v33_d60_force_rescue_once(obs, source_plan, overlap_mm)
                last = candidate
                cplan, cmotion, creport = candidate
                if cplan is not None and cmotion is not None:
                    return candidate
                crep = dict(creport or {})
                if int(crep.get('pair_trials', 0) or 0) > 0:
                    print(f'[D60-V33-RESCUE-STOP] overlap={float(overlap_mm):.0f}mm produced real pair trials but motion/safety validation rejected them')
                    return candidate
            return last

        def _d60_waist_endpoint_gate(self, obs, plan):
            metrics = dict(getattr(plan, 'metrics', {}) or {}) if plan is not None else {}
            if not bool(metrics.get('bottom_vla_v33_d60_rescue', False)):
                return super()._d60_waist_endpoint_gate(obs, plan)
            limits = dict(metrics.get('bottom_vla_v33_d60_rescue_limits', self._v33_d60_rescue_limits()))
            with self._v33_d60_rescue_lock:
                old = (float(self.front.d60_waist_grip_body_min_mm), float(self.front.d60_waist_grip_body_max_mm), float(self.front.d60_waist_grip_tangent_max_mm), float(self.front.d60_waist_grip_endpoint_radius_max_mm))
                try:
                    self.front.d60_waist_grip_body_min_mm = float(limits['body_min_mm'])
                    self.front.d60_waist_grip_body_max_mm = float(limits['body_max_mm'])
                    self.front.d60_waist_grip_tangent_max_mm = float(limits['tangent_max_mm'])
                    self.front.d60_waist_grip_endpoint_radius_max_mm = float(limits['radius_max_mm'])
                    ok, report = super()._d60_waist_endpoint_gate(obs, plan)
                finally:
                    self.front.d60_waist_grip_body_min_mm = old[0]
                    self.front.d60_waist_grip_body_max_mm = old[1]
                    self.front.d60_waist_grip_tangent_max_mm = old[2]
                    self.front.d60_waist_grip_endpoint_radius_max_mm = old[3]
            report = dict(report or {})
            report['bottom_vla_v33_d60_rescue'] = True
            report['bottom_vla_v33_d60_rescue_limits'] = dict(limits)
            return (ok, report)

        def _verify_sources_unchanged(self):
            changed = []
            base_checks = (('D50_BASKET_SWING_LAYDOWN', getattr(self, 'd50_path', None)), ('D54_OUTER_PULL', getattr(self, 'd54_path', None)), ('D55_PRESS_SWEEP', getattr(self, 'd55_path', None)), ('D56_WAIST_LIFT_LAYDOWN', getattr(self, 'd56_path', None)), ('D58_CIRC_POSITION', getattr(self, 'd58_path', None)))
            expected_map = getattr(self, 'source_sha256', {}) or {}
            for label, path in base_checks:
                expected = expected_map.get(label)
                if not path or not expected:
                    continue
                try:
                    current = v23._sha256(str(path))
                except Exception as exc:
                    changed.append(f'{label}:hash-error:{type(exc).__name__}')
                    continue
                if current != expected:
                    changed.append(label)
            extra_checks = (('ALIGN', source_paths.get('align'), getattr(self, 'align_source_sha256', None)), ('D60_DIRECT', source_paths.get('d60'), getattr(self, 'd60_source_sha256', None)), ('POSITION_ADJUST', source_paths.get('position'), getattr(self, 'position_source_sha256', None)))
            for label, path, expected in extra_checks:
                if not path or not expected:
                    continue
                try:
                    current = v23._sha256(str(path))
                except Exception as exc:
                    changed.append(f'{label}:hash-error:{type(exc).__name__}')
                    continue
                if current != expected:
                    changed.append(label)
            signature = tuple(changed)
            if changed and signature != self._v30_source_warning_signature:
                self._v30_source_warning_signature = signature
                print(f'[SOURCE-V30-WARN] on-disk source changed after startup: {changed}; current in-memory loaded modules remain fixed, so execution continues')
            return None

        def _v30_mask_info(self, locked):
            obs = getattr(locked, 'observation', None)
            mask = getattr(obs, 'mask', None) if obs is not None else None
            if mask is None:
                return {'valid': False, 'area_px': 0.0, 'source': 'NONE', 'fallback': False}
            area = None
            for value in (getattr(mask, 'area_px', None), getattr(mask, 'area', None)):
                try:
                    candidate = float(value)
                    if math.isfinite(candidate) and candidate > 0.0:
                        area = candidate
                        break
                except Exception:
                    pass
            if area is None:
                try:
                    mask_u8 = getattr(mask, 'mask_u8', None)
                    if mask_u8 is not None:
                        area = float(np.count_nonzero(np.asarray(mask_u8) > 0))
                except Exception:
                    area = None
            parts = []
            for obj in (mask, obs):
                for name in ('source', 'mask_source', 'class_name', 'reason', 'status', 'raw_status'):
                    value = getattr(obj, name, None)
                    if value is not None:
                        parts.append(str(value))
                for name in ('d30_mask_info', 'mask_info'):
                    value = getattr(obj, name, None)
                    if isinstance(value, dict):
                        for key in ('source', 'fallback', 'reason', 'raw_status', 'status'):
                            if value.get(key) is not None:
                                parts.append(str(value.get(key)))
            source = ' | '.join(parts)
            upper = source.upper()
            fallback = any((token in upper for token in ('FALLBACK_BGDIFF', 'CRUMPLED-FG', 'CRUMPLED', 'EMPTY-BOARD FOREGROUND', 'BOARD_BLOB_FALLBACK')))
            return {'valid': True, 'area_px': float(area or 0.0), 'source': source or 'MASK', 'fallback': bool(fallback)}

        def _v30_finalize_perception_status(self):
            with self.state_lock:
                locked = self.locked
            if locked is None:
                return
            info = self._v30_mask_info(locked)
            semantic = str(self.pending_semantic or self.semantic_selected or locked.action)
            if bool(info['valid']) and (not bool(info['fallback'])) and (float(info['area_px']) > 0.0):
                self._v30_last_trusted_mask_area_px = float(info['area_px'])
            if bool(getattr(locked, 'plan_ok', False)):
                return
            reason = str(getattr(locked, 'reason', '') or getattr(locked, 'planner_failure', '') or 'NO_SAFE_PLAN')
            if not bool(info['valid']):
                self.status = f'{semantic} RECOGNITION FAILED: {reason}'
                print(f'[PERCEPTION-V30] action={semantic} recognition=FAILED mask=NONE reason={reason}')
            else:
                self.status = f'{semantic} RECOGNITION OK / NO SAFE PLAN: {reason}'
                print(f"[PERCEPTION-V30] action={semantic} recognition=OK maskArea={float(info['area_px']):.0f}px planner=NO_SAFE_PLAN reason={reason}")

        def _prepare_action(self):
            action = str(self.selected_action or '')
            super()._prepare_action()
            with self.state_lock:
                locked = self.locked
            if locked is None:
                return
            info = self._v30_mask_info(locked)
            reference = self._v30_last_trusted_mask_area_px
            retry_actions = {'D54_OUTER_PULL', 'D55_PRESS_SWEEP'}
            undersized = bool(action in retry_actions and info['valid'] and info['fallback'] and (reference is not None) and (float(reference) >= 30000.0) and (float(info['area_px']) > 0.0) and (float(info['area_px']) < float(reference) * float(self._v30_fallback_min_ratio)))
            if undersized:
                ratio = float(info['area_px']) / max(float(reference), 1.0)
                print(f"[PERCEPTION-V30-RETRY] action={action} fallbackArea={float(info['area_px']):.0f}px trustedRef={float(reference):.0f}px ratio={ratio:.3f}<0.450; discard candidate and take one fresh snapshot")
                with self.state_lock:
                    self.locked = None
                    self.display_image = None
                    self.status = f'{action} SMALL FALLBACK MASK: FRESH RETRY'
                time.sleep(0.08)
                super()._prepare_action()
                with self.state_lock:
                    locked = self.locked
                if locked is None:
                    return
                info = self._v30_mask_info(locked)
                still_small = bool(info['valid'] and info['fallback'] and (float(info['area_px']) > 0.0) and (float(info['area_px']) < float(reference) * float(self._v30_fallback_min_ratio)))
                if still_small:
                    ratio = float(info['area_px']) / max(float(reference), 1.0)
                    locked.plan_ok = False
                    locked.planner_failure = 'UNTRUSTED_SMALL_FALLBACK_MASK'
                    locked.reason = f"fallback mask too small {float(info['area_px']):.0f}px vs trusted {float(reference):.0f}px ratio={ratio:.3f}"
                    locked.diagnostics = dict(getattr(locked, 'diagnostics', {}) or {})
                    locked.diagnostics.update({'v30_small_fallback_blocked': True, 'fallback_area_px': float(info['area_px']), 'last_trusted_area_px': float(reference), 'fallback_area_ratio': float(ratio)})
                    with self.state_lock:
                        self.locked = locked
                        self.status = f'{self.pending_semantic or action} RECOGNITION FAILED: FALLBACK MASK TOO SMALL'
                    print(f'[PERCEPTION-V30-BLOCK] action={action} second fallback still too small ratio={ratio:.3f}; auto dispatch disabled')
                    return
            self._v30_finalize_perception_status()

        def _finite_point2(self, value):
            try:
                arr = np.asarray(value, np.float64).reshape(-1)[:2]
                if arr.size == 2 and np.all(np.isfinite(arr)):
                    return arr.astype(np.float64)
            except Exception:
                pass
            return None

        def _pose_board_points(self, obs):
            pose = getattr(obs, 'pose', None)
            if pose is None:
                return {}
            out = {}
            aliases = {'waist_img_left': ('waist_img_left', 'waist_left'), 'waist_center': ('waist_center',), 'waist_img_right': ('waist_img_right', 'waist_right'), 'crotch': ('crotch', 'crotch_center'), 'img_left_hem_outer': ('img_left_hem_outer', 'left_hem_outer'), 'img_left_hem_inner': ('img_left_hem_inner', 'left_hem_inner'), 'img_right_hem_inner': ('img_right_hem_inner', 'right_hem_inner'), 'img_right_hem_outer': ('img_right_hem_outer', 'right_hem_outer')}
            for dict_name in ('keypoints_board', 'points_board', 'landmarks_board', 'refined_board'):
                d = getattr(pose, dict_name, None)
                if not isinstance(d, dict):
                    continue
                for canonical, names in aliases.items():
                    if canonical in out:
                        continue
                    for name in names:
                        p = self._finite_point2(d.get(name))
                        if p is not None:
                            out[canonical] = p
                            break
            for canonical, names in aliases.items():
                if canonical in out:
                    continue
                for name in names:
                    p = self._finite_point2(getattr(pose, name, None))
                    if p is not None:
                        out[canonical] = p
                        break
            for name in ('left_hem_center', 'right_hem_center', 'lower_center'):
                p = self._finite_point2(getattr(pose, name, None))
                if p is not None:
                    out[name] = p
            if 'left_hem_center' not in out and 'img_left_hem_outer' in out and ('img_left_hem_inner' in out):
                out['left_hem_center'] = 0.5 * (out['img_left_hem_outer'] + out['img_left_hem_inner'])
            if 'right_hem_center' not in out and 'img_right_hem_inner' in out and ('img_right_hem_outer' in out):
                out['right_hem_center'] = 0.5 * (out['img_right_hem_inner'] + out['img_right_hem_outer'])
            if 'lower_center' not in out and 'left_hem_center' in out and ('right_hem_center' in out):
                out['lower_center'] = 0.5 * (out['left_hem_center'] + out['right_hem_center'])
            return out

        def _align_vector_geometry(self, obs, seam_x=None):
            pts = self._pose_board_points(obs)
            waist = pts.get('waist_center')
            if waist is None and pts.get('waist_img_left') is not None and (pts.get('waist_img_right') is not None):
                waist = 0.5 * (pts['waist_img_left'] + pts['waist_img_right'])
            lower = pts.get('crotch')
            lower_source = 'CROTCH'
            if lower is None:
                lower = pts.get('lower_center')
                lower_source = 'LOWER_CENTER'
            if waist is None or lower is None:
                return None
            if seam_x is None:
                try:
                    seam_x = float(self.align._c93_taught_trace_calibration(self.config, self.align_args)['boundary_x_mm'])
                except Exception:
                    return None
            axis = lower - waist
            axis_len = float(np.linalg.norm(axis))
            if not math.isfinite(axis_len) or axis_len < 20.0:
                return None
            raw_angle = math.degrees(math.atan2(float(axis[0]), float(-axis[1])))
            angle_error = float((raw_angle + 90.0) % 180.0 - 90.0)
            mid = 0.5 * (waist + lower)
            waist_err = float(waist[0] - seam_x)
            lower_err = float(lower[0] - seam_x)
            mid_err = float(mid[0] - seam_x)
            return {'seam_x_mm': float(seam_x), 'waist_center': waist, 'lower_point': lower, 'lower_source': lower_source, 'midpoint': mid, 'axis_length_mm': axis_len, 'angle_error_deg': angle_error, 'waist_error_mm': waist_err, 'lower_error_mm': lower_err, 'mid_error_mm': mid_err, 'max_endpoint_error_mm': float(max(abs(waist_err), abs(lower_err)))}

        def _install_full_board_mask_roi(self):
            namespaces = []
            for name in ('args', 'd56_args', 'd54_args', 'd55_args', 'd58_args', 'align_args'):
                ns = getattr(self, name, None)
                if ns is None or any((id(ns) == id(existing) for existing in namespaces)):
                    continue
                namespaces.append(ns)
            changed = []
            for ns in namespaces:
                for key in ('d35_aruco_roi_inset_px', 'perception_roi_board_shrink_px', 'planning_mask_board_shrink_px', 'perception_board_shrink_px'):
                    if hasattr(ns, key):
                        old = getattr(ns, key)
                        setattr(ns, key, 0)
                        changed.append(f'{key}:{old}->0')
                if hasattr(ns, 'd35_strict_aruco_roi'):
                    setattr(ns, 'd35_strict_aruco_roi', True)
                if hasattr(ns, 'd32_board_roi'):
                    setattr(ns, 'd32_board_roi', True)
                if hasattr(ns, 'perception_roi_clip_to_aruco_board'):
                    setattr(ns, 'perception_roi_clip_to_aruco_board', True)
                if hasattr(ns, 'planning_mask_clip_to_board'):
                    setattr(ns, 'planning_mask_clip_to_board', True)
            unique = []
            for item in changed:
                if item not in unique:
                    unique.append(item)
            print('[MASK-V31-CONFIG] ' + (', '.join(unique) if unique else 'board ROI fields unavailable; source strict-board defaults retained'))

        def _install_d58_arm1_contact_z_offset(self):
            original = getattr(self.d58, 'contact_z', None)
            if not callable(original) or bool(getattr(original, '_bottom_vla_v30_arm1_z', False)):
                return
            offset = float(self._v30_d58_arm1_z_offset_mm)

            def wrapped(config, arm_key, args):
                value = float(original(config, arm_key, args))
                if str(arm_key).lower() == 'arm1':
                    value += offset
                return value
            wrapped._bottom_vla_v30_arm1_z = True
            self.d58.contact_z = wrapped

        def _install_align_surface_z_offset(self):
            offset = float(self._v30_align_surface_z_offset_mm)
            surface = getattr(self.align, '_c93_surface_z_at_board', None)
            if callable(surface) and (not bool(getattr(surface, '_bottom_vla_v30_z', False))):

                def surface_wrapped(*args, **kwargs):
                    return float(surface(*args, **kwargs)) + offset
                surface_wrapped._bottom_vla_v30_z = True
                self.align._c93_surface_z_at_board = surface_wrapped
                return
            contact = getattr(self.align, 'arm_contact_z', None)
            if callable(contact) and (not bool(getattr(contact, '_bottom_vla_v30_z', False))):

                def contact_wrapped(*args, **kwargs):
                    return float(contact(*args, **kwargs)) + offset
                contact_wrapped._bottom_vla_v30_z = True
                self.align.arm_contact_z = contact_wrapped

        def _install_align_centerline_policy(self):
            original = getattr(self.align, '_align7_build_auto_plan', None)
            if not callable(original) or bool(getattr(original, '_bottom_vla_v34_centerline', False)):
                return

            def get_kind(plan, decision):
                if isinstance(decision, dict):
                    for key in ('chosen', 'preferred', 'kind'):
                        value = decision.get(key)
                        if value is not None:
                            text = str(value).upper()
                            if text:
                                return text
                if isinstance(plan, dict):
                    for key in ('kind', 'chosen', 'preferred'):
                        value = plan.get(key)
                        if value is not None:
                            text = str(value).upper()
                            if text:
                                return text
                for key in ('kind', 'chosen', 'preferred'):
                    value = getattr(plan, key, None)
                    if value is not None:
                        text = str(value).upper()
                        if text:
                            return text
                return ''

            def set_ready(plan, ready):
                if plan is None:
                    return
                if isinstance(plan, dict):
                    if 'ready' in plan:
                        plan['ready'] = bool(ready)
                    if 'ok' in plan:
                        plan['ok'] = bool(ready)
                else:
                    for key in ('ready', 'ok'):
                        if hasattr(plan, key):
                            try:
                                setattr(plan, key, bool(ready))
                            except Exception:
                                pass

            def exact_target_safe(target):
                try:
                    q = np.asarray(target, np.float64).reshape(2)
                    if not np.all(np.isfinite(q)):
                        return (False, 'NONFINITE_TARGET')
                    marker_map = self.config.get('aruco', {}).get('marker_board_mm', {})
                    board = np.asarray(list(marker_map.values()), np.float64)
                    if board.ndim != 2 or board.shape[0] < 3 or board.shape[1] < 2:
                        return (False, 'BOARD_BOUNDS_UNAVAILABLE')
                    margin = 15.0
                    xmin = float(np.min(board[:, 0])) + margin
                    xmax = float(np.max(board[:, 0])) - margin
                    ymin = float(np.min(board[:, 1])) + margin
                    ymax = float(np.max(board[:, 1])) - margin
                    if not (xmin <= float(q[0]) <= xmax and ymin <= float(q[1]) <= ymax):
                        return (False, f'BOARD_MARGIN x=[{xmin:.1f},{xmax:.1f}] y=[{ymin:.1f},{ymax:.1f}]')
                    dual = self.config.get('dual_roarm', {})
                    split_x = float(dual.get('split_board_x', 324.5))
                    dead = float(getattr(self.align_cfg, 'center_dead_half_width', getattr(self.cfg56, 'center_dead_half_width', 25.0)))
                    arm2_max_x = split_x - max(0.0, dead)
                    if float(q[0]) > arm2_max_x:
                        return (False, f'ARM2_PRIVATE_X>{arm2_max_x:.1f}')
                    return (True, 'OK')
                except Exception as exc:
                    return (False, f'SAFETY_ERROR:{repr(exc)}')

            def apply_exact(plan, decision, geom):
                if not isinstance(plan, dict):
                    return (False, 'PLAN_NOT_DICT')
                source = self._finite_point2(plan.get('source_board'))
                if source is None:
                    return (False, 'SOURCE_UNAVAILABLE')
                mid_err = float(geom['mid_error_mm'])
                target = np.asarray([float(source[0]) - mid_err, float(source[1])], np.float64)
                safe, why = exact_target_safe(target)
                if not safe:
                    return (False, why)
                delta = target - source
                move_mm = float(np.linalg.norm(delta))
                fields = {'target_board': [float(target[0]), float(target[1])], 'requested_target_board': [float(target[0]), float(target[1])], 'center_delta_board': [float(delta[0]), float(delta[1])], 'move_mm': move_mm, 'target_fraction': 1.0, 'target_reason': 'V34_EXACT_CENTERLINE_REMAINING_DISTANCE', 'predicted_angle_residual_deg': float(geom['angle_error_deg']), 'predicted_seam_residual_mm': 0.0, 'angle_gain': 0.0, 'v34_exact_centerline_translation': True, 'v34_mid_error_mm': mid_err}
                plan.update(fields)
                candidates = decision.get('candidates')
                if isinstance(candidates, list):
                    for cand in candidates:
                        if isinstance(cand, dict) and str(cand.get('kind', '')).upper() == 'WAIST':
                            cand.update(copy.deepcopy(fields))
                decision.update({'chosen': 'WAIST', 'preferred': 'WAIST', 'reason': 'CENTER_VECTOR_PARALLEL_EXACT_REMAINING_DISTANCE', 'v34_exact_centerline_translation': True, 'v34_exact_move_mm': move_mm, 'v34_exact_target_board': [float(target[0]), float(target[1])], 'v34_native_move_cap_bypassed': True})
                print(f"[ALIGN-V34-EXACT] midErr={mid_err:+.1f}mm endpointGap={abs(float(geom['waist_error_mm']) - float(geom['lower_error_mm'])):.1f}mm angle={float(geom['angle_error_deg']):+.1f}deg move={move_mm:.1f}mm source=({float(source[0]):.1f},{float(source[1]):.1f}) target=({float(target[0]):.1f},{float(target[1]):.1f})")
                return (True, 'OK')

            def wrapped(obs, H, waist, seam_x, correction_count, config, cfg, args):
                geom = self._align_vector_geometry(obs, seam_x)
                effective_count = max(1, int(correction_count))
                plan, decision = original(obs, H, waist, seam_x, effective_count, config, cfg, args)
                decision = dict(decision or {}) if isinstance(decision, dict) else {'reason': str(decision)}
                kind = get_kind(plan, decision)
                if geom is None:
                    decision.update({'v34_objective': 'WAIST_CROTCH_WHITE_LINE', 'v34_geometry_available': False, 'v34_effective_correction_count': effective_count, 'v34_first_waist_bias_removed': True, 'v34_native_selector': True})
                    print(f"[ALIGN-V34] geometry unavailable; native align-11 result={kind or 'NONE'} reason={decision.get('reason', '-')}")
                    return (plan, decision)
                mid_err = float(geom['mid_error_mm'])
                max_end = float(geom['max_endpoint_error_mm'])
                angle_err = float(geom['angle_error_deg'])
                waist_err = float(geom['waist_error_mm'])
                lower_err = float(geom['lower_error_mm'])
                endpoint_gap = abs(waist_err - lower_err)
                lateral_abs = abs(mid_err)
                angle_abs = abs(angle_err)
                aligned = bool(lateral_abs <= float(self._v30_align_line_done_mm) and angle_abs <= float(self._v30_align_angle_done_deg))
                if aligned:
                    set_ready(plan, False)
                    plan = None
                    decision.update({'chosen': None, 'preferred': 'NONE', 'reason': 'V34_ALREADY_ALIGNED', 'v34_already_aligned': True})
                same_side = bool(waist_err * lower_err > 0.0)
                exact_candidate = bool(plan is not None and str(kind).upper() == 'WAIST' and (not aligned) and (angle_abs <= float(self._v30_align_angle_done_deg)) and same_side and (endpoint_gap <= 30.0) and (lateral_abs > float(self._v30_align_line_done_mm)))
                exact_applied = False
                exact_reason = 'NOT_CANDIDATE'
                if exact_candidate:
                    exact_applied, exact_reason = apply_exact(plan, decision, geom)
                    if not exact_applied:
                        print(f'[ALIGN-V34-EXACT-BLOCK] midErr={mid_err:+.1f}mm angle={angle_err:+.1f}deg endpointGap={endpoint_gap:.1f}mm reason={exact_reason}; native safe plan preserved')
                decision.update({'v34_objective': 'WAIST_CROTCH_WHITE_LINE', 'v34_geometry_available': True, 'v34_effective_correction_count': effective_count, 'v34_first_waist_bias_removed': True, 'v34_native_selector': not exact_applied, 'v34_lower_source': str(geom['lower_source']), 'v34_exact_candidate': exact_candidate, 'v34_exact_applied': exact_applied, 'v34_exact_reason': exact_reason, 'white_line_x_mm': float(geom['seam_x_mm']), 'vector_mid_x_mm': float(geom['midpoint'][0]), 'white_line_mid_error_mm': mid_err, 'white_line_waist_error_mm': waist_err, 'white_line_lower_error_mm': lower_err, 'white_line_max_endpoint_error_mm': max_end, 'center_angle_error_deg': angle_err})
                selected = str(decision.get('chosen') or kind or 'NONE').upper()
                move_value = None
                if plan is not None:
                    try:
                        move_value = float(plan.get('move_mm')) if isinstance(plan, dict) else float(getattr(plan, 'move_mm'))
                    except Exception:
                        move_value = None
                print(f"[ALIGN-V34-ENDPOINT] lower={geom['lower_source']} waistErr={waist_err:+.1f}mm lowerErr={lower_err:+.1f}mm midErr={mid_err:+.1f}mm angleErr={angle_err:+.1f}deg chosen={selected} move={('NA' if move_value is None else f'{move_value:.1f}mm')} exact={exact_applied} count={effective_count} aligned={aligned}")
                return (plan, decision)
            wrapped._bottom_vla_v34_centerline = True
            self.align._align7_build_auto_plan = wrapped

        def _prepare_align(self):
            old_finish = float(self.front.align_finish_angle_deg)
            old_dual_trigger = float(self.front.align_dual_waist_min_pull_mm)
            try:
                self.front.align_finish_angle_deg = -1.0
                self.front.align_dual_waist_min_pull_mm = 1000000000.0
                print(f'[ALIGN-V34-CENTER] targetX uses fresh center-vector white-line geometry; dualWaistYTrigger={float(self.front.align_dual_waist_min_pull_mm):.1f}mm')
                return super()._prepare_align()
            finally:
                self.front.align_finish_angle_deg = old_finish
                self.front.align_dual_waist_min_pull_mm = old_dual_trigger

        def _candidate_board_center(self, cand, H):
            g = cand.get('d21_geometry', {}) if isinstance(cand, dict) else {}
            if isinstance(g, dict):
                p = self._finite_point2(g.get('center_board'))
                if p is not None:
                    return p
            p = self._finite_point2(cand.get('center_board')) if isinstance(cand, dict) else None
            if p is not None:
                return p
            if isinstance(cand, dict):
                px = self._finite_point2(cand.get('center_px'))
                fn = getattr(self.d55, 'pixel_to_board', None)
                if px is not None and callable(fn):
                    try:
                        return self._finite_point2(fn(H, float(px[0]), float(px[1])))
                    except Exception:
                        pass
            return None

        def _candidate_board_normal(self, cand):
            if not isinstance(cand, dict):
                return None
            g = cand.get('d21_geometry', {})
            if isinstance(g, dict):
                n = self._finite_point2(g.get('normal_board'))
                if n is not None:
                    nn = float(np.linalg.norm(n))
                    if nn > 1e-06:
                        return n / nn
                t = self._finite_point2(g.get('tangent_board'))
                if t is not None:
                    tn = float(np.linalg.norm(t))
                    if tn > 1e-06:
                        t = t / tn
                        return np.asarray([-t[1], t[0]], np.float64)
            return None

        def _fold_recovery_geometry(self, obs, H, candidates):
            pts = self._pose_board_points(obs)
            waist = pts.get('waist_center')
            crotch = pts.get('crotch')
            left = pts.get('left_hem_center')
            right = pts.get('right_hem_center')
            if any((x is None for x in (waist, crotch, left, right))):
                return None
            left_len = float(np.linalg.norm(left - crotch))
            right_len = float(np.linalg.norm(right - crotch))
            if min(left_len, right_len) < 25.0 or max(left_len, right_len) < 1e-06:
                return None
            leg_balance = float(min(left_len, right_len) / max(left_len, right_len))
            left_width = None
            right_width = None
            if pts.get('img_left_hem_outer') is not None and pts.get('img_left_hem_inner') is not None:
                left_width = float(np.linalg.norm(pts['img_left_hem_outer'] - pts['img_left_hem_inner']))
            if pts.get('img_right_hem_inner') is not None and pts.get('img_right_hem_outer') is not None:
                right_width = float(np.linalg.norm(pts['img_right_hem_outer'] - pts['img_right_hem_inner']))
            hem_balance = 1.0
            if left_width is not None and right_width is not None and (max(left_width, right_width) > 1e-06):
                hem_balance = float(min(left_width, right_width) / max(left_width, right_width))
            folded = bool(leg_balance < 0.7 or hem_balance < 0.58)
            if not folded:
                return None
            folded_side = 'left' if left_len <= right_len else 'right'
            folded_hem = left if folded_side == 'left' else right
            other_hem = right if folded_side == 'left' else left
            body = crotch - waist
            body_n = float(np.linalg.norm(body))
            leg = folded_hem - crotch
            leg_n = float(np.linalg.norm(leg))
            if body_n < 20.0 or leg_n < 20.0:
                return None
            body_u = body / body_n
            leg_u = leg / leg_n
            proj = waist + body_u * float(np.dot(folded_hem - waist, body_u))
            outward = folded_hem - proj
            outward_n = float(np.linalg.norm(outward))
            if outward_n < 8.0:
                side = np.asarray([-body_u[1], body_u[0]], np.float64)
                if float(np.dot(side, folded_hem - crotch)) < 0.0:
                    side = -side
                outward_u = side
            else:
                outward_u = outward / outward_n
            desired = 0.68 * leg_u + 0.62 * outward_u
            desired_n = float(np.linalg.norm(desired))
            if desired_n < 1e-06:
                return None
            desired = desired / desired_n
            folded_lateral = abs(float(body_u[0] * (folded_hem - waist)[1] - body_u[1] * (folded_hem - waist)[0]))
            folded_cross = float(body_u[0] * (folded_hem - crotch)[1] - body_u[1] * (folded_hem - crotch)[0])
            recovery = []
            boundary_ids = set()
            for index, cand in enumerate(candidates):
                center = self._candidate_board_center(cand, H)
                normal = self._candidate_board_normal(cand)
                if center is None:
                    continue
                rel = center - crotch
                t = float(np.dot(rel, leg) / max(leg_n * leg_n, 1e-06))
                lateral = abs(float(body_u[0] * (center - waist)[1] - body_u[1] * (center - waist)[0]))
                cross = float(body_u[0] * rel[1] - body_u[1] * rel[0])
                same_side = bool(abs(folded_cross) < 5.0 or abs(cross) < 5.0 or folded_cross * cross > 0.0)
                central_limit = max(14.0, 0.3 * folded_lateral)
                if lateral <= central_limit and 0.0 <= t <= 0.82:
                    boundary_ids.add(index)
                    continue
                if not same_side or t < 0.1 or t > 1.15 or (normal is None):
                    continue
                normal_align = float(abs(np.dot(normal, desired)))
                if normal_align < 0.55:
                    continue
                major = max(0.0, float(cand.get('major_length_px', 0.0) or 0.0))
                linearity = max(1.0, float(cand.get('linearity', 1.0) or 1.0))
                center_bias = 1.0 - min(1.0, abs(t - 0.58) / 0.58)
                score = 110.0 * normal_align + 30.0 * center_bias + min(30.0, major / 6.0) + min(15.0, (linearity - 1.0) * 5.0)
                recovery.append((score, index, cand, center, normal, t))
            recovery.sort(key=lambda x: x[0], reverse=True)
            return {'folded_side': folded_side, 'leg_balance': leg_balance, 'hem_balance': hem_balance, 'waist': waist, 'crotch': crotch, 'folded_hem': folded_hem, 'other_hem': other_hem, 'body_u': body_u, 'body_len': body_n, 'desired': desired, 'recovery': recovery, 'boundary_ids': boundary_ids}

        def _d55_build_perpendicular_plan(self, obs, heat, H, config, cfg, args):
            candidates = list(getattr(heat, 'candidates', []) or []) if heat is not None else []
            geom = self._fold_recovery_geometry(obs, H, candidates) if candidates else None
            if geom is None:
                return super()._d55_build_perpendicular_plan(obs, heat, H, config, cfg, args)
            desired = np.asarray(geom['desired'], np.float64).reshape(2)
            for _, index, cand, center, normal, t in list(geom['recovery'])[:5]:
                try:
                    local_heat = copy.copy(heat)
                    local_heat.candidates = [copy.deepcopy(cand)]
                    plan = super()._d55_build_perpendicular_plan(obs, local_heat, H, config, cfg, args)
                except Exception:
                    continue
                if plan is None or not bool(getattr(plan, 'ok', False)):
                    continue
                arm_points = dict(getattr(plan, 'arm_points', {}) or {})
                moving_key = None
                support_key = None
                actual_u = None
                active_t = None
                support_t = None
                for arm_key, points in arm_points.items():
                    if not isinstance(points, dict):
                        continue
                    src = self._finite_point2(points.get('source_board'))
                    dst = self._finite_point2(points.get('target_board'))
                    if src is None or dst is None:
                        continue
                    move = dst - src
                    move_n = float(np.linalg.norm(move))
                    role = str(points.get('role', '')).lower()
                    body_t = float(np.dot(src - geom['waist'], geom['body_u']) / max(float(geom['body_len']), 1e-06))
                    if move_n > 5.0:
                        moving_key = arm_key
                        actual_u = move / move_n
                        active_t = body_t
                    elif 'support' in role or 'anchor' in role or move_n <= 1.0:
                        support_key = arm_key
                        support_t = body_t
                if moving_key is None or support_key is None or actual_u is None:
                    continue
                direction_alignment = float(np.dot(actual_u, desired))
                upper_support_ok = bool(active_t is not None and support_t is not None and (support_t <= active_t - 0.04) and (support_t <= 0.78))
                if direction_alignment < 0.45 or not upper_support_ok:
                    continue
                metrics = dict(getattr(plan, 'metrics', {}) or {})
                metrics.update({'d55v30_internal_mode': 'FOLDED_LEG_RECOVERY', 'd55v30_folded_side': str(geom['folded_side']), 'd55v30_leg_balance': float(geom['leg_balance']), 'd55v30_hem_balance': float(geom['hem_balance']), 'd55v30_candidate_original_index': int(index), 'd55v30_candidate_center_board': [float(center[0]), float(center[1])], 'd55v30_desired_sweep_unit': [float(desired[0]), float(desired[1])], 'd55v30_actual_direction_alignment': direction_alignment, 'd55v30_upper_support_ok': upper_support_ok, 'd55v30_fold_boundary_excluded_count': int(len(geom['boundary_ids']))})
                plan.metrics = metrics
                plan.arm_points[moving_key]['role'] = 'folded_leg_outward_downward_sweep'
                plan.arm_points[support_key]['role'] = 'folded_leg_upper_support_anchor'
                print(f"[D55-V30-FOLDED-LEG-RECOVERY] side={geom['folded_side']} leg={geom['leg_balance']:.2f} hem={geom['hem_balance']:.2f} candidate={index + 1} active={str(moving_key).upper()} support={str(support_key).upper()} dirAlign={direction_alignment:.2f}")
                return plan
            safe_candidates = [cand for i, cand in enumerate(candidates) if i not in geom['boundary_ids']]
            if safe_candidates:
                local_heat = copy.copy(heat)
                local_heat.candidates = safe_candidates
                plan = super()._d55_build_perpendicular_plan(obs, local_heat, H, config, cfg, args)
                if plan is not None:
                    metrics = dict(getattr(plan, 'metrics', {}) or {})
                    metrics.update({'d55v30_internal_mode': 'NORMAL_WRINKLE_FOLD_BOUNDARY_FILTERED', 'd55v30_folded_side': str(geom['folded_side']), 'd55v30_leg_balance': float(geom['leg_balance']), 'd55v30_hem_balance': float(geom['hem_balance']), 'd55v30_fold_boundary_excluded_count': int(len(geom['boundary_ids']))})
                    plan.metrics = metrics
                print(f"[D55-V30-FOLD-FALLBACK] no safe outward/downward recovery; excluded={len(geom['boundary_ids'])} boundary candidates, normal non-boundary planner used")
                return plan
            module = self.d55
            print(f"[D55-V30-FOLD-BLOCKED] folded state detected but no safe recovery/non-boundary wrinkle candidate; excluded={len(geom['boundary_ids'])}")
            return module.DualWrinkleStretchPlan(False, 'D55-V30 folded state: no safe FOLDED_LEG_RECOVERY', metrics={'d55_failure_category': 'NO_SAFE_FOLDED_LEG_RECOVERY', 'd55v30_internal_mode': 'FOLDED_LEG_RECOVERY_BLOCKED', 'd55v30_folded_side': str(geom['folded_side']), 'd55v30_leg_balance': float(geom['leg_balance']), 'd55v30_hem_balance': float(geom['hem_balance']), 'd55v30_fold_boundary_excluded_count': int(len(geom['boundary_ids']))})

        def _auto_state_dict(self, state):
            names = list(state.get('names', []))
            values = list(state.get('values', []))
            return {str(k): float(values[i]) for i, k in enumerate(names) if i < len(values)}

        def _fold_midvector_asymmetry(self, obs):
            pts = self._pose_board_points(obs)
            waist = pts.get('waist_center')
            if waist is None and pts.get('waist_img_left') is not None and pts.get('waist_img_right') is not None:
                waist = 0.5 * (pts['waist_img_left'] + pts['waist_img_right'])
            crotch = pts.get('crotch')
            left = pts.get('left_hem_center')
            right = pts.get('right_hem_center')
            if any(x is None for x in (waist, crotch, left, right)):
                return None
            axis = crotch - waist
            axis_n = float(np.linalg.norm(axis))
            if axis_n < 20.0:
                return None
            u = axis / axis_n
            n = np.asarray([-u[1], u[0]], np.float64)
            left_signed = float(np.dot(left - crotch, n))
            right_signed = float(np.dot(right - crotch, n))
            left_abs = abs(left_signed)
            right_abs = abs(right_signed)
            lateral_max = max(left_abs, right_abs)
            if lateral_max < 15.0:
                return None
            lateral_balance = float(min(left_abs, right_abs) / max(lateral_max, 1.0))
            magnitude_asym = float(1.0 - lateral_balance)
            midpoint = 0.5 * (left + right)
            mean_lateral = max(0.5 * (left_abs + right_abs), 1.0)
            midpoint_offset_norm = float(abs(np.dot(midpoint - crotch, n)) / mean_lateral)
            same_side = bool(left_signed * right_signed >= 0.0)
            asymmetry = float(max(magnitude_asym, min(1.0, midpoint_offset_norm)))
            if same_side:
                asymmetry = max(asymmetry, 0.75)
            return {'asymmetry': float(min(1.0, asymmetry)), 'magnitude_asymmetry': magnitude_asym, 'midpoint_offset_norm': midpoint_offset_norm, 'left_signed_mm': left_signed, 'right_signed_mm': right_signed, 'same_side': same_side}

        def _auto_choose_semantic(self, obs, bundle):
            probe = SimpleNamespace(obs=obs, bundle=bundle, H=self.H_raw.copy())
            state = self._build_bottom_state_v2(probe)
            f = self._auto_state_dict(state)
            mask_valid = f.get('mask_valid', 0.0)
            center_err = f.get('board_center_error_norm', 1.0)
            width = f.get('mask_width_norm', 0.0)
            height = f.get('mask_height_norm', 0.0)
            solidity = f.get('mask_solidity', 0.0)
            extent = f.get('mask_extent', 0.0)
            pose_valid = f.get('pose_valid', 0.0)
            leg_balance = f.get('leg_length_balance', 1.0)
            hem_balance = f.get('hem_width_balance', 1.0)
            symmetry_err = f.get('pose_left_right_symmetry_error_norm', 0.0)
            waist_y_err = f.get('waist_target_y_error_norm', 0.0)
            body_angle = abs(f.get('body_axis_angle_norm', 0.0))
            waist_angle = abs(f.get('waist_axis_angle_norm', 0.0))
            wrinkle_edge = f.get('wrinkle_edge_ratio', 0.0)
            wrinkle_len = f.get('dominant_wrinkle_length_norm', 0.0)
            wrinkle_lin = f.get('dominant_wrinkle_linearity_norm', 0.0)
            if mask_valid < 0.5:
                return (None, 'mask invalid -> REJUDGE required', state)
            if center_err > 0.145:
                return ('POSITION_ADJUST', f'board center error={center_err:.3f}', state)
            folded_mid = self._fold_midvector_asymmetry(obs)
            heavy_fold = bool(pose_valid >= 0.5 and (leg_balance < float(self._submission_fold_leg_balance_threshold) or hem_balance < float(self._submission_fold_hem_balance_threshold)))
            if heavy_fold and folded_mid is not None and float(folded_mid['asymmetry']) >= float(self._submission_midvector_asym_threshold):
                return ('WAIST_PULL_LAYDOWN', f"heavy fold + center-vector asymmetry leg={leg_balance:.2f} hem={hem_balance:.2f} midAsym={float(folded_mid['asymmetry']):.2f} left={float(folded_mid['left_signed_mm']):+.1f}mm right={float(folded_mid['right_signed_mm']):+.1f}mm", state)
            folded_like = bool(pose_valid >= 0.5 and (leg_balance < 0.7 or hem_balance < 0.58 or symmetry_err > 0.3))
            strong_wrinkle = bool(wrinkle_len >= 0.11 and wrinkle_lin >= 0.1 and (wrinkle_edge >= 0.01))
            press_reason = None
            if folded_like:
                press_reason = f'fold/asymmetry leg={leg_balance:.2f} hem={hem_balance:.2f} sym={symmetry_err:.2f}'
            elif strong_wrinkle:
                press_reason = f'wrinkle len={wrinkle_len:.3f} lin={wrinkle_lin:.3f} edge={wrinkle_edge:.3f}'
            press_guard = bool(press_reason is not None and int(self._submission_consecutive_press) >= int(self._submission_press_repeat_limit))
            if press_reason is not None and not press_guard:
                return ('PRESS_SWEEP', press_reason, state)
            needs_spread = bool(width < 0.48 or extent < 0.38 or solidity < 0.6 or (height < 0.42))
            guard_prefix = f'PRESS repeat guard {int(self._submission_consecutive_press)}/{int(self._submission_press_repeat_limit)}; ' if press_guard else ''
            if needs_spread:
                return ('OUTER_PULL', guard_prefix + f'spread width={width:.3f} height={height:.3f} extent={extent:.3f} solidity={solidity:.3f}', state)
            if pose_valid >= 0.5 and waist_y_err < -0.075:
                return ('WAIST_PULL_LAYDOWN', guard_prefix + f'waist target y error={waist_y_err:.3f}', state)
            align_geom = self._align_vector_geometry(obs)
            if align_geom is not None:
                mid_error = abs(float(align_geom['mid_error_mm']))
                max_endpoint_error = float(align_geom['max_endpoint_error_mm'])
                if mid_error > float(self._v30_align_line_done_mm) or max_endpoint_error > float(self._v30_align_large_endpoint_error_mm):
                    return ('ALIGN', guard_prefix + f'white-line mid={mid_error:.1f}mm maxEnd={max_endpoint_error:.1f}mm', state)
            if body_angle > 0.065 or waist_angle > 0.075:
                return ('ALIGN', guard_prefix + f'axis body={body_angle:.3f} waist={waist_angle:.3f}', state)
            if press_guard:
                return (None, f'PRESS_SWEEP_REPEAT_GUARD count={int(self._submission_consecutive_press)} reason={press_reason}; no non-PRESS structural action is currently eligible', state)
            return ('FINISH', f'finish center={center_err:.3f} body={body_angle:.3f} waist={waist_angle:.3f}', state)

        def _auto_judge_next(self, trigger, epoch=None):
            if epoch is None:
                epoch = int(self._submission_cycle_epoch)
            with self._auto_judge_lock:
                if self._auto_judge_busy:
                    print('[AUTO-JUDGE] already running')
                    return
                self._auto_judge_busy = True
            try:
                with self._submission_cycle_lock:
                    if not self._submission_cycle_active or int(epoch) != int(self._submission_cycle_epoch):
                        print(f'[AUTO-JUDGE] stale cycle trigger={trigger} epoch={epoch}')
                        return
                    if self._submission_dispatch_pending:
                        print('[AUTO-JUDGE] blocked by pending dispatch')
                        return
                with self.state_lock:
                    if self.motion_busy or self.inference_busy:
                        print('[AUTO-JUDGE] blocked by active motion/inference')
                        return
                    self.status = f'AUTO JUDGE: FRESH SNAPSHOT ({trigger})'
                if not self.empty_baseline_ready:
                    self._submission_block('EMPTY_BOARD_BASELINE_REQUIRED')
                    return
                if not self._ensure_camera_clear('AUTO_JUDGE_BEFORE_NEXT', allow_move=False):
                    self._submission_block('CAMERA_CLEAR_NOT_VERIFIED')
                    return
                bundle = self._capture_i_frame_from_live('D56_WAIST_LIFT_LAYDOWN')
                obs = self._infer_for_action('D56_WAIST_LIFT_LAYDOWN', bundle.corrected)
                semantic, reason, state = self._auto_choose_semantic(obs, bundle)
                if semantic is None:
                    self.auto_recommended = 'REJUDGE'
                    print(f'[AUTO-JUDGE] trigger={trigger} action=REJUDGE reason={reason}')
                    self._submission_retry_or_block('REJUDGE', str(reason), int(epoch))
                    return
                self.auto_recommended = semantic
                print(f'[AUTO-JUDGE] trigger={trigger} action={semantic} reason={reason}')
                if not self._select_semantic(semantic, origin='AUTO'):
                    self._submission_block(f'SEMANTIC_PREPARE_START_FAILED:{semantic}')
            except Exception as exc:
                print(f'[AUTO-JUDGE-ERROR] {exc!r}')
                self._submission_block(f'AUTO_JUDGE_EXCEPTION:{type(exc).__name__}:{exc}')
            finally:
                with self._auto_judge_lock:
                    self._auto_judge_busy = False

        def _schedule_auto_judge(self, trigger, delay=0.05, epoch=None):
            if epoch is None:
                epoch = int(self._submission_cycle_epoch)

            def worker():
                if delay > 0.0:
                    time.sleep(delay)
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    with self._submission_cycle_lock:
                        active = bool(self._submission_cycle_active and int(epoch) == int(self._submission_cycle_epoch))
                        dispatch_pending = bool(self._submission_dispatch_pending)
                    if not active:
                        return
                    with self.state_lock:
                        blocked = bool(self.motion_busy or self.inference_busy)
                    if not blocked and (not dispatch_pending):
                        self._auto_judge_next(trigger, int(epoch))
                        return
                    time.sleep(0.05)
                self._submission_block(f'AUTO_JUDGE_WAIT_TIMEOUT:{trigger}')
            threading.Thread(target=worker, name=f'bottom-submission-auto-judge-e{int(epoch)}', daemon=True).start()

        def _schedule_forced_semantic(self, semantic, trigger, delay=0.05, epoch=None):
            if epoch is None:
                epoch = int(self._submission_cycle_epoch)

            def worker():
                if delay > 0.0:
                    time.sleep(delay)
                deadline = time.monotonic() + 10.0
                while time.monotonic() < deadline:
                    with self._submission_cycle_lock:
                        active = bool(self._submission_cycle_active and int(epoch) == int(self._submission_cycle_epoch))
                        dispatch_pending = bool(self._submission_dispatch_pending)
                    if not active:
                        return
                    with self.state_lock:
                        blocked = bool(self.motion_busy or self.inference_busy)
                    if not blocked and not dispatch_pending:
                        self.auto_recommended = str(semantic)
                        self.status = f'AUTO FORCED: {semantic} ({trigger})'
                        print(f'[AUTO-FORCED] trigger={trigger} action={semantic}')
                        if not self._select_semantic(str(semantic), origin='AUTO-FORCED'):
                            self._submission_block(f'FORCED_SEMANTIC_PREPARE_START_FAILED:{semantic}')
                        return
                    time.sleep(0.05)
                self._submission_block(f'FORCED_SEMANTIC_WAIT_TIMEOUT:{trigger}:{semantic}')
            threading.Thread(target=worker, name=f'bottom-submission-forced-{str(semantic).lower()}-e{int(epoch)}', daemon=True).start()

        def _basket_verify_gripper(self, target, tolerance, attempts, settle, stage):
            if str(stage) != 'BASKET-CLOSE-VERIFY':
                return super()._basket_verify_gripper(target, tolerance, attempts, settle, stage)
            min_close = 2.8
            last_fb = None
            last_actual = None
            for attempt in range(1, max(1, int(attempts)) + 1):
                self._basket_set_gripper(float(target), 0.0, f'{stage}_{attempt}')
                time.sleep(max(0.0, float(settle)))
                fb = self._basket_feedback(quiet=True)
                if fb is None or 't' not in fb:
                    print(f'[{stage}-V33] attempt={attempt} feedback unavailable')
                    continue
                last_fb = fb
                last_actual = float(fb['t'])
                error = abs(last_actual - float(target))
                accepted = last_actual >= min_close
                print(f'[{stage}-V33] attempt={attempt} target={float(target):.3f} actual={last_actual:.3f} error={error:.3f}rad minClose={min_close:.3f} accepted={accepted}')
                if accepted:
                    return fb
            raise RuntimeError(f'{stage} failed minClose={min_close:.3f} actual={last_actual} feedback={last_fb}')

        def _basket_return_arm2_standby(self, release_verified):
            if not release_verified:
                raise RuntimeError('ARM2 standby blocked until release is verified')
            target = np.asarray([float(self.front.basket_arm2_standby_x), float(self.front.basket_arm2_standby_y), float(self.front.basket_arm2_standby_z)], dtype=np.float64)
            tool_t = float(self.front.basket_arm2_standby_t)
            speed = float(self.front.basket_standby_speed)
            tolerance = float(self.front.basket_move_tolerance_mm)
            attempts = 4
            last_xyz = None
            last_error = float('inf')
            for attempt in range(1, attempts + 1):
                print(f'[BASKET-STANDBY-V33] command attempt={attempt}/{attempts} target=({target[0]:.1f},{target[1]:.1f},{target[2]:.1f})')
                self._basket_move_goal(float(target[0]), float(target[1]), float(target[2]), tool_t, speed, f'BASKET_ARM2_STANDBY_RETRY_{attempt}')
                deadline = time.monotonic() + 2.5
                while time.monotonic() < deadline:
                    time.sleep(max(0.15, min(0.35, float(self.front.basket_move_poll_s))))
                    fb = self._basket_feedback(quiet=True)
                    if fb is None or not all((k in fb for k in ('x', 'y', 'z'))):
                        continue
                    last_xyz = np.asarray([float(fb['x']), float(fb['y']), float(fb['z'])], dtype=np.float64)
                    last_error = float(np.linalg.norm(last_xyz - target))
                    print(f'[BASKET-STANDBY-V33] attempt={attempt} error={last_error:.1f}mm actual=({last_xyz[0]:.1f},{last_xyz[1]:.1f},{last_xyz[2]:.1f})')
                    if last_error <= tolerance:
                        return last_xyz
            raise RuntimeError(f'BASKET ARM2 standby failed after {attempts} T104 commands error={last_error:.1f}mm actual={(None if last_xyz is None else last_xyz.tolist())}')

        def _submission_print_provenance(self):
            import inspect
            rows = []
            rows.append(('ENTRY', str(Path(__file__).resolve())))
            rows.append(('BASE', str(Path(source_paths['base']).resolve())))
            rows.append(('D50', str(Path(getattr(self, 'd50_path', '')).resolve())))
            rows.append(('D54', str(Path(getattr(self, 'd54_path', '')).resolve())))
            rows.append(('D55', str(Path(getattr(self, 'd55_path', '')).resolve())))
            rows.append(('D60', str(Path(source_paths['d60']).resolve())))
            rows.append(('D58', str(Path(source_paths['position']).resolve())))
            rows.append(('ALIGN', str(Path(source_paths['align']).resolve())))
            for label, module in (('E49', getattr(self.d54, 'e49_bottom', None)), ('E62', getattr(self.d54, 'e62_bottom', None)), ('D25', getattr(self.d54, 'd25v2', None))):
                path = getattr(module, '__file__', None)
                if path:
                    rows.append((label, str(Path(path).resolve())))
            cam_path = inspect.getsourcefile(self.undistorter.__class__)
            if cam_path:
                rows.append(('CAMERA_UNDISTORT', str(Path(cam_path).resolve())))
            print('[SUBMISSION-PROVENANCE] sys.path-head=' + repr(sys.path[:6]))
            for label, path in rows:
                try:
                    digest = v23._sha256(path)
                except Exception:
                    digest = 'UNAVAILABLE'
                print(f'[SUBMISSION-PROVENANCE] {label} file={path} sha256={digest}')

        def _submission_plan_id(self, locked):
            return f"{str(getattr(locked, 'action', ''))}:{float(getattr(locked, 'created_at', 0.0)):.6f}:{id(locked)}"

        def _submission_start_cycle(self):
            with self._submission_cycle_lock:
                if self._submission_cycle_active:
                    print('[AUTO-START] ignored: cycle already active')
                    return
                with self.state_lock:
                    if self.motion_busy or self.inference_busy:
                        print('[AUTO-START] blocked: worker active')
                        return
                if not self.empty_baseline_ready:
                    self.status = 'SYSTEM READY REQUIRES E EMPTY-BOARD BASELINE'
                    print('[AUTO-START] blocked: press E on empty board first')
                    return
                self._submission_cycle_epoch += 1
                epoch = int(self._submission_cycle_epoch)
                self._submission_cycle_active = True
                self._submission_dispatch_pending = False
                self._submission_last_dispatched_plan_id = None
                self._submission_reason_counts.clear()
                self._submission_blocked_reason = ''
                self._submission_finished = False
                self._submission_consecutive_press = 0
            self._prepare_generation += 1
            self._invalidate_for_new_action('NEW_SUBMISSION_CYCLE')
            self.auto_recommended = 'BASKET_GRASP'
            self.status = f'AUTO RUNNING EPOCH={epoch}: BASKET_GRASP'
            print(f'[AUTO-START] epoch={epoch} first=BASKET_GRASP')
            if not self._select_semantic('BASKET_GRASP', origin='START'):
                self._submission_block('BASKET_PREPARE_START_FAILED')

        def _submission_block(self, reason):
            reason = str(reason)
            with self._submission_cycle_lock:
                if not self._submission_cycle_active and self._submission_blocked_reason == reason:
                    return
                self._submission_cycle_active = False
                self._submission_cycle_epoch += 1
                self._submission_dispatch_pending = False
                self._submission_blocked_reason = reason
                self._submission_finished = False
            with self.state_lock:
                self._prepare_generation += 1
                self.locked = None
                self.semantic_selected = None
                self.pending_semantic = None
                self.selected_action = None
                self.status = f'AUTO BLOCKED: {reason} | NEW X REQUIRED'
            with self.align_runtime_lock:
                self.align_runtime.clear()
            with self.d60_runtime_lock:
                self.d60_runtime.clear()
            print(f'[AUTO-BLOCKED] reason={reason} operator intervention required; new X required')

        def _submission_retry_or_block(self, semantic, reason, epoch):
            key = f'{str(semantic)}:{str(reason)}'
            count = int(self._submission_reason_counts.get(key, 0)) + 1
            self._submission_reason_counts[key] = count
            if count < int(self._submission_auto_rejudge_limit):
                with self.state_lock:
                    self.locked = None
                    self.semantic_selected = None
                    self.pending_semantic = None
                    self.selected_action = None
                    self.status = f'AUTO REJUDGE {count}/{int(self._submission_auto_rejudge_limit) - 1}: {reason}'
                print(f'[AUTO-REJUDGE] semantic={semantic} count={count} reason={reason}')
                self._schedule_auto_judge(f'retry_{str(semantic).lower()}', 0.15, int(epoch))
                return
            self._submission_block(f'REPEATED_{str(semantic)}:{reason}')

        def _submission_after_prepare(self, semantic, generation, epoch, stale):
            if stale:
                return
            with self._submission_cycle_lock:
                if not self._submission_cycle_active or int(epoch) != int(self._submission_cycle_epoch):
                    return
            with self.state_lock:
                locked = self.locked
            if locked is None:
                self._submission_retry_or_block(semantic, 'NO_FROZEN_PLAN', int(epoch))
                return
            expected = v23.SEMANTIC_TO_INTERNAL.get(str(semantic))
            if expected is None or str(getattr(locked, 'action', '')) != str(expected):
                self._submission_block(f"SEMANTIC_BINDING_MISMATCH:{semantic}:{getattr(locked, 'action', None)}")
                return
            if not bool(getattr(locked, 'plan_ok', False)):
                reason = str(getattr(locked, 'planner_failure', None) or getattr(locked, 'reason', 'NO_SAFE_PLAN'))
                self._submission_retry_or_block(semantic, reason, int(epoch))
                return
            self._submission_dispatch_locked(str(semantic), int(epoch))

        def _submission_dispatch_locked(self, semantic, epoch):
            with self._submission_cycle_lock:
                if not self._submission_cycle_active or int(epoch) != int(self._submission_cycle_epoch):
                    return
                if self._submission_dispatch_pending:
                    self._submission_block('DUPLICATE_DISPATCH_PENDING')
                    return
            with self.state_lock:
                if self.motion_busy or self.inference_busy:
                    self._submission_block('DISPATCH_WHILE_WORKER_ACTIVE')
                    return
                locked = self.locked
            if locked is None or not bool(getattr(locked, 'plan_ok', False)):
                self._submission_block('DISPATCH_WITHOUT_VALID_FROZEN_PLAN')
                return
            expected = v23.SEMANTIC_TO_INTERNAL.get(str(semantic))
            if str(getattr(locked, 'action', '')) != str(expected):
                self._submission_block(f"DISPATCH_BINDING_MISMATCH:{semantic}:{getattr(locked, 'action', None)}")
                return
            if not self.empty_baseline_ready:
                self._submission_block('DISPATCH_EMPTY_BASELINE_MISSING')
                return
            age = time.time() - float(locked.created_at)
            if age > float(self.args.locked_plan_max_age_s):
                self._submission_block(f'FROZEN_PLAN_STALE:{age:.1f}s')
                return
            try:
                self._verify_sources_unchanged()
            except Exception as exc:
                self._submission_block(f'SOURCE_VALIDATION_FAILED:{exc}')
                return
            plan_id = self._submission_plan_id(locked)
            with self._submission_cycle_lock:
                if plan_id == self._submission_last_dispatched_plan_id:
                    self._submission_block('DUPLICATE_FROZEN_PLAN_DISPATCH')
                    return
                self._submission_dispatch_pending = True
                self._submission_last_dispatched_plan_id = plan_id
            self.status = f'AUTO DISPATCH: {semantic} EXACT FROZEN PLAN'
            print(f'[AUTO-APPROVAL] epoch={epoch} semantic={semantic} plan={plan_id} age={age:.2f}s')
            super()._start_execution()
            if str(getattr(locked, 'action', '')) == 'FINISH':
                return
            time.sleep(0.03)
            with self.state_lock:
                started = bool(self.motion_busy or (self.worker is not None and self.worker.is_alive()))
            if not started:
                with self._submission_cycle_lock:
                    self._submission_dispatch_pending = False
                self._submission_block(f'DISPATCH_NOT_STARTED:{semantic}')

        def _submission_after_action_complete(self, action, success, sent, detail, locked):
            semantic = v23.INTERNAL_TO_SEMANTIC.get(str(action), str(action))
            with self._submission_cycle_lock:
                if not self._submission_cycle_active:
                    return
                epoch = int(self._submission_cycle_epoch)
                self._submission_dispatch_pending = False
            with self.state_lock:
                self.locked = None
                self.semantic_selected = None
                self.pending_semantic = None
                self.selected_action = None
                self.status = f'AUTO ACTION COMPLETE: {semantic}' if success else f'AUTO ACTION FAILED: {semantic} {detail}'
            if not bool(success):
                self._submission_block(f'PHYSICAL_ACTION_FAILED:{semantic}:{detail}')
                return
            if semantic == 'PRESS_SWEEP':
                self._submission_consecutive_press += 1
            else:
                self._submission_consecutive_press = 0
            print(f'[AUTO-ACTION-HISTORY] completed={semantic} consecutivePress={int(self._submission_consecutive_press)}')
            if semantic == 'BASKET_GRASP' and bool(self._submission_force_position_after_basket):
                print(f'[AUTO-CONTINUE] epoch={epoch} completed=BASKET_GRASP -> forced POSITION_ADJUST')
                self._schedule_forced_semantic('POSITION_ADJUST', 'after_basket_grasp', 0.2, epoch)
                return
            print(f'[AUTO-CONTINUE] epoch={epoch} completed={semantic} -> fresh AUTO-JUDGE')
            self._schedule_auto_judge(f'after_{semantic.lower()}', 0.08, epoch)

        def _submission_finish_terminal(self, locked):
            with self._submission_cycle_lock:
                self._submission_cycle_active = False
                self._submission_cycle_epoch += 1
                self._submission_dispatch_pending = False
                self._submission_last_dispatched_plan_id = None
                self._submission_finished = True
                self._submission_blocked_reason = ''
            with self.state_lock:
                self._prepare_generation += 1
                self.locked = None
                self.semantic_selected = None
                self.pending_semantic = None
                self.selected_action = None
                self.inference_busy = False
                self.inference_action = None
                self.motion_busy = False
                self.display_image = locked.frame.raw.copy()
                self.status = 'FINISH: AUTO CYCLE DISARMED | NEW X REQUIRED'
            with self.align_runtime_lock:
                self.align_runtime.clear()
            with self.d60_runtime_lock:
                self.d60_runtime.clear()
            self.last_executed_semantic = 'FINISH'
            print('[FINISH-TERMINAL] garment motion=0; scheduler disarmed; stale workers invalidated; new X required')

        def _submission_handle(self, event):
            event = str(event).upper()
            if event == 'START':
                self._submission_start_cycle()
                return
            if event == 'EMPTY_BASELINE':
                with self._submission_cycle_lock:
                    active = self._submission_cycle_active
                with self.state_lock:
                    busy = self.motion_busy or self.inference_busy
                if active or busy:
                    print('[E] blocked during active auto cycle')
                    return
                self._capture_empty_board()
                return
            if event == 'LOCK_H':
                with self._submission_cycle_lock:
                    active = self._submission_cycle_active
                with self.state_lock:
                    busy = self.motion_busy or self.inference_busy
                if active or busy:
                    print('[H] blocked during active auto cycle')
                    return
                self._lock_and_save_homography()
                return
            if event == 'QUIT':
                with self.state_lock:
                    if self.motion_busy:
                        print('[QUIT] blocked while robot motion is running')
                        return
                with self._submission_cycle_lock:
                    self._submission_cycle_active = False
                    self._submission_cycle_epoch += 1
                    self._submission_dispatch_pending = False
                self._prepare_generation += 1
                if self.args.mode == 'physical':
                    print('[QUIT] returning ARM1/ARM2 to standby before normal shutdown')
                    if not self._ensure_camera_clear('NORMAL_QUIT', allow_move=True):
                        print('[QUIT-WARN] standby verification failed')
                self.closed = True

        def _draw_submission_overlay(self, image):
            canvas = image.copy()
            with self._submission_cycle_lock:
                active = bool(self._submission_cycle_active)
                epoch = int(self._submission_cycle_epoch)
                blocked = str(self._submission_blocked_reason)
                finished = bool(self._submission_finished)
            with self.state_lock:
                semantic = str(self.pending_semantic or self.semantic_selected or 'IDLE')
                busy = bool(self.motion_busy)
                infer = bool(self.inference_busy)
                status = str(self.status)
            if finished:
                mode = 'FINISH'
            elif blocked:
                mode = 'BLOCKED'
            elif active:
                mode = 'AUTO RUNNING'
            else:
                mode = 'SYSTEM READY'
            self.cv2.putText(canvas, f'{mode} | epoch={epoch} | {semantic}', (20, 40), self.cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)
            self.cv2.putText(canvas, f'motion={busy} inference={infer}', (20, 68), self.cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2)
            self.cv2.putText(canvas, status[:150], (20, canvas.shape[0] - 45), self.cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            self.cv2.putText(canvas, 'X START | E EMPTY | L LOCK H | Q/ESC QUIT', (20, canvas.shape[0] - 18), self.cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2)
            return canvas

        def run(self):
            window = getattr(self.args, 'display', 'BOTTOM FULL AUTO')
            try:
                self.cv2.namedWindow(window, self.cv2.WINDOW_NORMAL)
                self.cv2.resizeWindow(window, int(self.args.width), int(self.args.height))
            except Exception as exc:
                print(f'[UI-WARN] window setup failed: {exc!r}')
            print('[KEYS] X START FULL-AUTO | E EMPTY BASELINE | L LOCK H | Q/ESC QUIT')
            print(f'[MODE] {self.args.mode} submission_full_auto=True')
            try:
                while not self.closed:
                    ok, raw = self._read_raw(flush=0)
                    if not ok or raw is None:
                        print('[CAM] read failed')
                        self._submission_block('CAMERA_READ_FAILED')
                        break
                    corrected = self._frame_for_action(raw, self.selected_action)
                    with self.live_frame_lock:
                        self.latest_live_raw = raw.copy()
                        self.latest_live_corrected = corrected.copy()
                        self.latest_live_monotonic = time.monotonic()
                    with self.state_lock:
                        shown = self.display_image.copy() if self.display_image is not None else raw.copy()
                    self.cv2.imshow(window, self._draw_submission_overlay(shown))
                    key = self.cv2.waitKey(1) & 255
                    if key in (ord('x'), ord('X')):
                        self._submission_handle('START')
                    elif key in (ord('e'), ord('E')):
                        self._submission_handle('EMPTY_BASELINE')
                    elif key in (ord('l'), ord('L')):
                        self._submission_handle('LOCK_H')
                    elif key in (ord('q'), ord('Q'), 27):
                        self._submission_handle('QUIT')
                return 0
            finally:
                self.close()

        def close(self):
            with self._submission_cycle_lock:
                self._submission_cycle_active = False
                self._submission_cycle_epoch += 1
                self._submission_dispatch_pending = False
            self._prepare_generation += 1
            super().close()
    return BottomVLAApp

def main():
    front, remaining = v23._parse_front(sys.argv[1:])
    front.auto_prepare_next = True
    sources = v23._resolve_sources(front)
    base, align_mod, args = v23._build_runtime(front, remaining, sources)
    cls = _make_app_class(base, align_mod, front, sources)
    app = cls(args)
    return app.run()
if __name__ == '__main__':
    raise SystemExit(main())
