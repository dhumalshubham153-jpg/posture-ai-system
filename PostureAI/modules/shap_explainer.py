import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

class ShapExplainer:

    FEATURES = [
        'neck_forward_angle',
        'shoulder_slope',
        'rounded_shoulder_angle',
        'pelvic_tilt',
        'spine_deviation',
    ]

    LABELS = [
        'Neck Angle',
        'Shoulder Slope',
        'Rounded Shoulder',
        'Pelvic Tilt',
        'Spine Deviation',
    ]

    def __init__(self, model):
        self.model    = model
        self.explainer= None
        os.makedirs('reports', exist_ok=True)

    def setup(self, X_background=None):
        """Setup SHAP explainer with background data"""
        if X_background is None:
            # Use synthetic background
            np.random.seed(42)
            X_background = np.array([
                [10, 5,  165, 5,  10],
                [20, 15, 140, 15, 30],
                [35, 30, 110, 30, 60],
            ])
        self.explainer = shap.TreeExplainer(self.model.model)

    def explain(self, features):
        """Get SHAP values for a single prediction"""
        if self.explainer is None:
            self.setup()

        vals = []
        for feat in self.FEATURES:
            v = features.get(feat)
            vals.append(float(v) if v is not None else 0.0)

        X          = np.array([vals])
        shap_vals  = self.explainer.shap_values(X)

        # Handle multi-class
        if isinstance(shap_vals, list):
            # Use class with highest impact
            shap_arr = np.array(shap_vals)
            sv = shap_arr[:, 0, :].mean(axis=0)
        else:
            sv = shap_vals[0]

        explanation = []
        for i, feat in enumerate(self.FEATURES):
            explanation.append({
                'feature'   : self.LABELS[i],
                'value'     : round(vals[i], 2),
                'shap_value': round(float(sv[i]), 4),
                'impact'    : 'increases risk' if sv[i] > 0 else 'decreases risk',
            })

        # Sort by absolute impact
        explanation.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        return explanation

    def plot(self, features, save_path='reports/shap_plot.png'):
        """Generate and save SHAP bar chart"""
        explanation = self.explain(features)

        labels = [e['feature']    for e in explanation]
        values = [e['shap_value'] for e in explanation]
        colors = ['#f87171' if v > 0 else '#34d399' for v in values]

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#0a0f1e')
        ax.set_facecolor('#0a0f1e')

        bars = ax.barh(labels, values, color=colors, edgecolor='none', height=0.5)

        ax.set_xlabel('SHAP Value (Impact on Risk)',
                      color='white', fontsize=10)
        ax.set_title('Why is your posture scored this way?',
                     color='white', fontsize=12, pad=12)
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.axvline(0, color='#475569', linewidth=0.8)

        for bar, val in zip(bars, values):
            ax.text(
                val + (0.002 if val >= 0 else -0.002),
                bar.get_y() + bar.get_height() / 2,
                f'{val:+.3f}',
                va='center',
                ha='left' if val >= 0 else 'right',
                color='white', fontsize=8
            )

        plt.tight_layout()
        plt.savefig(save_path, dpi=120,
                    facecolor='#0a0f1e', bbox_inches='tight')
        plt.close()
        return save_path