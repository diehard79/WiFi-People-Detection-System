# ML/AI Model Requirements - WiFi People Detection System

**Version:** 1.0
**Last Updated:** 2026-02-02
**Status:** Requirements Complete

---

## 1. Model Requirements Overview

### 1.1 Problem Types

The WiFi People Detection System addresses two distinct ML problems:

**Binary Classification - Presence Detection**
- **Goal:** Determine if at least one person is present in a room
- **Classes:** Empty (0 people), Occupied (1+ people)
- **Criticality:** High - safety and security applications
- **Performance Target:** >99% accuracy

**Multi-class Classification - People Counting**
- **Goal:** Determine exact number of people (0-5, extendable to 9)
- **Classes:** 0, 1, 2, 3, 4, 5 people (extension to 6, 7, 8, 9)
- **Criticality:** Medium - occupancy management and analytics
- **Performance Target:** 98-99% accuracy with 4+ detectors

### 1.2 Performance Targets

| Metric | Presence Detection | People Counting | Measurement Method |
|--------|-------------------|-----------------|-------------------|
| **Overall Accuracy** | >99% | 98-99% (4+ detectors) | Holdout test set |
| **Precision** | >99% | 95-98% per class | Per-class metrics |
| **Recall** | >99% | 95-98% per class | Per-class metrics |
| **F1 Score** | >0.99 | 0.95-0.98 | Weighted average |
| **False Positive Rate** | <1% | <2% | Confusion matrix |
| **False Negative Rate** | <1% | <2% | Confusion matrix |
| **End-to-End Latency** | <25 seconds | <25 seconds | Real-time measurement |
| **Model Inference Time** | <100ms | <500ms | Per prediction |
| **Memory Footprint** | <5MB | <20MB | Serialized model |

### 1.3 Latency Requirements

**End-to-End Detection Pipeline:**
```
Data Collection (20s window) → Feature Extraction (1s) → Model Inference (<1s) → Result Display (<1s)
Total: <25 seconds (including 20s data window)
```

**Real-Time Constraints:**
- Data window: 20 seconds (minimum viable detection window)
- Feature computation: <1 second for 4 detectors
- Model prediction: <100ms (presence), <500ms (counting)
- API response: <2 seconds total
- UI update: <500ms after receiving result

**Performance SLAs:**
- 95th percentile latency: <20 seconds (excluding 20s window)
- 99th percentile latency: <25 seconds
- Maximum acceptable latency: 30 seconds

### 1.4 Training Data Requirements

**Minimum Viable Dataset:**
- Presence Detection: 300 samples (150 empty, 150 occupied)
- People Counting: 1000 samples (balanced across 0-5 classes)

**Recommended Production Dataset:**
- Presence Detection: 2000+ samples
- People Counting: 5000+ samples
- Continuous collection: 100+ samples per week

**Data Quality Standards:**
- Label accuracy: >99% (verified by human spot-checks)
- Sampling rate: 1 Hz (1 sample per second per detector)
- Signal quality: RSSI range -30 to -90 dBm
- Missing data tolerance: <5% per 20-second window

---

## 2. Presence Detection Model

### 2.1 Algorithm Selection

**Primary Approach: Statistical Thresholding + Logistic Regression**

**Rationale:**
- Simplicity and interpretability
- Fast training and inference
- Excellent performance (>99%) achieved in research
- Easy to recalibrate daily

**Alternative Algorithms Considered:**
| Algorithm | Accuracy | Training Time | Inference Speed | Interpretability | Selected? |
|-----------|----------|---------------|-----------------|------------------|-----------|
| Logistic Regression | 99.2% | Fast (<1s) | Very fast (<10ms) | High | ✅ Yes |
| Random Forest | 99.5% | Medium (10s) | Fast (<50ms) | Medium | No |
| SVM | 99.3% | Medium (5s) | Fast (<20ms) | Low | No |
| Neural Network | 99.6% | Slow (60s) | Medium (<100ms) | Low | No |

### 2.2 Input Features

**Primary Features (Required):**
1. **Standard Deviation of RSSI** (Most Important)
   - Computed over 20-second window (20 samples at 1 Hz)
   - Calculated per detector
   - Aggregated: max(std_dev) across all detectors
   - Rationale: Human movement creates signal variation

2. **Mean RSSI Value**
   - Average signal strength over window
   - Per detector and global mean
   - Rationale: Bodies attenuate WiFi signals

3. **RSSI Variance**
   - Squared deviation from mean
   - Complementary to std_dev
   - Captures signal volatility

**Secondary Features (Optional Enhancement):**
4. **RSSI Skewness**
   - Third standardized moment
   - Detects asymmetric signal distribution
   - Indicates directional movement

5. **RSSI Kurtosis**
   - Fourth standardized moment
   - Detects heavy-tailed distributions
   - Indicates sporadic movement

6. **Multi-Detector Correlation**
   - Pearson correlation between detector pairs
   - Human presence affects all detectors similarly
   - Range: -1 to 1 (high correlation = likely occupied)

**Feature Computation Window:**
- Default: 20 seconds (20 samples at 1 Hz)
- Minimum: 10 seconds (reduced accuracy)
- Maximum: 30 seconds (increased latency, minimal gain)

### 2.3 Training Approach

**Semi-Supervised Learning Strategy:**

**Phase 1: Noise Training (Empty Room)**
- Collect 20 minutes of RSSI data from empty room
- Compute feature statistics (std_dev, mean, variance)
- Establish "empty room" baseline
- Train threshold using percentile method (e.g., 95th percentile)

**Phase 2: Calibration (One-Time Setup)**
- Collect 10 minutes with 1 person (stationary + moving)
- Compute feature statistics for occupied state
- Train logistic regression model
- Validate threshold on held-out data

**Phase 3: Daily Recalibration**
- Automatic: Collect 5 minutes of "likely empty" data (nighttime)
- Update threshold using moving average (exponential decay)
- Manual: Trigger recalibration via admin UI
- Validation: Compare predictions against known occupancy

**Training Algorithm: Logistic Regression**

```python
# Pseudocode for presence detection training
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Features: [std_dev, mean, variance, skewness, kurtosis, correlation]
X_train = []  # Feature matrix (n_samples, n_features)
y_train = []  # Labels: 0 (empty), 1 (occupied)

# Create pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', LogisticRegression(
        C=1.0,  # Regularization strength
        class_weight='balanced',  # Handle imbalanced data
        max_iter=1000,
        random_state=42
    ))
])

# Train model
pipeline.fit(X_train, y_train)

# Predict with threshold
y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
threshold = 0.5  # Default, can be tuned
y_pred = (y_pred_proba >= threshold).astype(int)
```

**Training Frequency:**
- Initial training: Once during setup
- Recalibration: Daily (automatic) + on-demand (manual)
- Full retraining: Weekly or when accuracy drops

### 2.4 Performance Metrics

**Target Metrics:**

| Metric | Target | Acceptable Minimum | Measurement |
|--------|--------|-------------------|-------------|
| **Accuracy** | >99% | >98% | Correct predictions / Total predictions |
| **Precision** | >99% | >98% | TP / (TP + FP) |
| **Recall (Sensitivity)** | >99% | >98% | TP / (TP + FN) |
| **Specificity** | >99% | >98% | TN / (TN + FP) |
| **F1 Score** | >0.99 | >0.98 | 2 × (Precision × Recall) / (Precision + Recall) |
| **AUC-ROC** | >0.99 | >0.98 | Area under ROC curve |
| **False Positive Rate** | <1% | <2% | FP / (FP + TN) |
| **False Negative Rate** | <1% | <2% | FN / (FN + TP) |

**Confusion Matrix (Expected):**

```
                 Predicted Empty    Predicted Occupied
Actual Empty          99%                  1%
Actual Occupied        1%                  99%
```

**Per-Class Performance:**
- Empty Room (Class 0): Precision >99%, Recall >99%
- Occupied (Class 1): Precision >99%, Recall >99%

**Error Analysis:**
- False Positives: Typically due to environmental factors (pets, HVAC)
- False Negatives: Typically due to very still occupants or signal dead zones

### 2.5 Model Size and Deployment Constraints

**Model Serialization:**
- Format: Python pickle (`.pkl`) or joblib
- Model size: <1 MB (Logistic Regression with 6 features)
- Dependencies: scikit-learn, numpy, scipy
- Compatibility: Python 3.8+, scikit-learn 1.0+

**Deployment Options:**

| Deployment Type | Pros | Cons | Recommended? |
|----------------|------|------|--------------|
| **Edge (Local Python)** | Low latency, no internet needed, privacy | Requires Python runtime | ✅ Primary |
| **Edge (ONNX)** | Cross-platform, faster inference | More complex build process | Optional |
| **Cloud (API)** | Centralized updates, easy scaling | Higher latency, privacy concerns | Backup |

**Edge Device Requirements:**
- CPU: Any modern processor (1 GHz+)
- RAM: 512 MB minimum
- Storage: 10 MB for model + dependencies
- Python: 3.8+ with scikit-learn

**Optimization Techniques:**
- Model quantization (float32 → int8): 4x size reduction
- Feature computation caching: Reduce redundant calculations
- Batch prediction: Process multiple windows together
- Lazy loading: Load model only when needed

---

## 3. People Counting Model

### 3.1 Algorithm Selection

**Primary Approach: Random Forest Classifier**

**Rationale:**
- Handles non-linear relationships well
- Robust to outliers and noisy features
- Built-in feature importance
- Excellent performance (98-99%) in research
- Handles multi-class classification natively

**Alternative Algorithms Considered:**
| Algorithm | Accuracy | Training Time | Inference Speed | Interpretability | Selected? |
|-----------|----------|---------------|-----------------|------------------|-----------|
| Random Forest | 98.5% | Medium (30s) | Fast (<100ms) | High | ✅ Yes |
| Gradient Boosting | 99.0% | Slow (120s) | Medium (<200ms) | Medium | No |
| Neural Network | 99.2% | Slow (180s) | Medium (<150ms) | Low | No |
| SVM (One-vs-Rest) | 97.5% | Medium (60s) | Medium (<150ms) | Low | No |
| k-NN | 96.0% | Instant | Slow (<500ms) | High | No |

### 3.2 Input Features

**Feature Categories:**

**1. Time-Domain Features (Per Detector)**
- Mean, Median, Mode
- Standard Deviation, Variance
- Minimum, Maximum, Range
- Skewness, Kurtosis
- Interquartile Range (IQR)
- Mean Absolute Deviation (MAD)

**2. Frequency-Domain Features (Per Detector)**
- FFT coefficients (top 10 magnitudes)
- Dominant frequency (peak FFT bin)
- Spectral centroid
- Spectral entropy
- Band power (5 frequency bands)
- Harmonic distortion ratio

**3. Cross-Detector Correlation Features**
- Pairwise Pearson correlation (n_detectors choose 2)
- Pairwise Spearman correlation
- Average correlation across all pairs
- Maximum correlation
- Correlation variance

**4. Temporal Features**
- Autocorrelation (lag 1-5)
- Difference between consecutive windows
- Rolling statistics (5-second sub-windows)
- Trend coefficient (linear regression slope)

**5. Aggregate Features**
- Mean of features across detectors
- Standard deviation of features across detectors
- Max, min, range of features across detectors
- Detector count (variable)

**Feature Count:**
- With 4 detectors: ~150-200 features
- With 8 detectors: ~300-400 features
- After feature selection: ~50-100 features

### 3.3 Training Approach

**Supervised Learning Strategy:**

**Data Collection Protocol:**

For each class (0, 1, 2, 3, 4, 5 people):
1. **Stationary Phase:** 10 minutes
   - People positioned randomly in room
   - Minimal movement (reading, working)
   - 5 different configurations (layouts)

2. **Movement Phase:** 10 minutes
   - People walking around room
   - Varied speeds and directions
   - Simulating real-world activity

3. **Edge Cases:** 5 minutes
   - People near detector (worst case)
   - People far from detector (best case)
   - People grouped together
   - People spread apart

Total data collection: 25 people × 2 phases × 3 classes = ~150 minutes
Total samples: 150 min × 3 windows/min = 450 samples per class
Total dataset: 450 × 6 classes = 2700 samples

**Cross-Validation Strategy:**

```python
# Pseudocode for training Random Forest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Create pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('feature_selection', SelectKBest(
        score_func=f_classif,
        k=100  # Select top 100 features
    )),
    ('classifier', RandomForestClassifier(
        n_estimators=200,  # Number of trees
        max_depth=20,  # Prevent overfitting
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',  # Consider sqrt(n_features) per split
        bootstrap=True,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1  # Use all CPU cores
    ))
])

# Cross-validation (k=3)
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='accuracy')

print(f"CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

# Train final model on all data
pipeline.fit(X_train, y_train)
```

**Feature Importance Analysis:**

```python
# Extract feature importances
feature_importances = pipeline.named_steps['classifier'].feature_importances_
selected_features = pipeline.named_steps['feature_selection'].get_support()

# Plot top 20 features
top_indices = np.argsort(feature_importances)[::-1][:20]
plt.barh(range(20), feature_importances[top_indices])
plt.yticks(range(20), feature_names[top_indices])
plt.xlabel('Feature Importance')
plt.title('Top 20 Features for People Counting')
plt.show()
```

**Model Versioning:**

```
models/
├── counting_v1.0.pkl (Initial model, 4 detectors)
├── counting_v1.1.pkl (Retrained with more data)
├── counting_v2.0.pkl (Extended to 9 classes)
└── counting_v2.1.pkl (Optimized hyperparameters)
```

**Retraining Strategy:**
- **Scheduled:** Weekly automatic retraining with new data
- **Performance-based:** Trigger when accuracy drops below 95%
- **Data-based:** Trigger when 500+ new samples collected
- **Major updates:** Quarterly with algorithm improvements

### 3.4 Performance Metrics

**Target Metrics (Overall):**

| Metric | Target (4+ detectors) | Acceptable (2-3 detectors) | Measurement |
|--------|----------------------|---------------------------|-------------|
| **Overall Accuracy** | 98-99% | 95-97% | Correct / Total |
| **Weighted F1 Score** | >0.97 | >0.94 | Weighted average |
| **Macro F1 Score** | >0.95 | >0.90 | Unweighted average |

**Per-Class Performance (Expected with 4 detectors):**

| Class | Precision | Recall | F1 Score | Support |
|-------|-----------|--------|----------|---------|
| 0 people | 99.2% | 99.5% | 0.994 | 450 samples |
| 1 person | 98.5% | 98.0% | 0.983 | 450 samples |
| 2 people | 98.0% | 97.5% | 0.978 | 450 samples |
| 3 people | 97.5% | 97.0% | 0.972 | 450 samples |
| 4 people | 97.0% | 96.5% | 0.967 | 450 samples |
| 5 people | 96.5% | 96.0% | 0.962 | 450 samples |

**Confusion Matrix (Expected):**

```
Predicted →     0     1     2     3     4     5
Actual ↓
0             447     3     0     0     0     0
1               5   441     4     0     0     0
2               0     7   438     5     0     0
3               0     0     9   437     4     0
4               0     0     0    12   432     6
5               0     0     0     0    18   432
```

**Error Patterns:**
- Most common: Off-by-1 errors (e.g., predict 2 instead of 3)
- Least common: Large errors (e.g., predict 0 instead of 5)
- Edge cases: High counts (4-5) slightly less accurate
- Impact: Error magnitude typically ±1 person

**Detector Count Impact:**

| Detectors | Accuracy | Training Time | Inference Time | Recommended? |
|-----------|----------|---------------|----------------|--------------|
| 1 | 85-90% | Fast | Fast | ❌ No |
| 2 | 92-95% | Fast | Fast | ⚠️ Minimum |
| 3 | 95-97% | Medium | Fast | ✅ Viable |
| 4 | 98-99% | Medium | Fast | ✅ Optimal |
| 5+ | 98-99% | Slow | Medium | ⚠️ Diminishing returns |

### 3.5 Model Versioning and Retraining Strategy

**Version Control:**

```yaml
# Model metadata file (model_metadata.yaml)
model_id: "counting_v2.1"
algorithm: "RandomForestClassifier"
version: "2.1"
created_at: "2026-02-02T10:00:00Z"
training_samples: 5000
accuracy: 0.985
classes: [0, 1, 2, 3, 4, 5]
features: 150
hyperparameters:
  n_estimators: 200
  max_depth: 20
  min_samples_split: 5
dependencies:
  scikit-learn: "1.0.2"
  numpy: "1.21.0"
```

**A/B Testing Framework:**
- Deploy new model to 10% of traffic
- Monitor accuracy and latency for 7 days
- Compare against baseline (current model)
- Roll back if accuracy drops >1%

**Retraining Triggers:**

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Scheduled | Weekly | Automatic retraining |
| Accuracy Drop | <95% on validation set | Immediate retraining |
| New Data | +500 samples | Next scheduled retraining |
| Drift Detection | Feature distribution shift >10% | Investigate + retrain |
| User Feedback | >10 complaints/day | Immediate investigation |

**Model Rollback Strategy:**
- Keep last 5 model versions
- Automatic rollback if accuracy drops >2% post-deployment
- Manual rollback via admin interface
- 24-hour monitoring period after deployment

---

## 4. Feature Engineering Pipeline

### 4.1 Time-Domain Features

**Statistical Moments (Per Detector):**

```python
import numpy as np
from scipy import stats

def compute_time_domain_features(rssi_window):
    """
    Compute time-domain features from RSSI window (20 samples)

    Args:
        rssi_window: Array of 20 RSSI values (1 detector)

    Returns:
        Dictionary of 12 time-domain features
    """
    features = {}

    # Central tendency
    features['mean'] = np.mean(rssi_window)
    features['median'] = np.median(rssi_window)
    features['mode'] = stats.mode(rssi_window, keepdims=True)[0][0]

    # Dispersion
    features['std_dev'] = np.std(rssi_window)
    features['variance'] = np.var(rssi_window)
    features['min'] = np.min(rssi_window)
    features['max'] = np.max(rssi_window)
    features['range'] = features['max'] - features['min']

    # Shape
    features['skewness'] = stats.skew(rssi_window)
    features['kurtosis'] = stats.kurtosis(rssi_window)

    # Robust statistics
    q75, q25 = np.percentile(rssi_window, [75, 25])
    features['iqr'] = q75 - q25
    features['mad'] = np.mean(np.abs(rssi_window - features['mean']))

    return features
```

**For 4 detectors:**
- Total time-domain features: 12 features × 4 detectors = **48 features**

### 4.2 Frequency-Domain Features

**FFT-Based Features (Per Detector):**

```python
from scipy.fft import fft, fftfreq
from scipy.signal import periodogram

def compute_frequency_domain_features(rssi_window, sample_rate=1):
    """
    Compute frequency-domain features from RSSI window

    Args:
        rssi_window: Array of 20 RSSI values
        sample_rate: 1 Hz (1 sample per second)

    Returns:
        Dictionary of 15 frequency-domain features
    """
    features = {}
    n = len(rssi_window)

    # Compute FFT
    fft_values = fft(rssi_window)
    fft_magnitudes = np.abs(fft_values)
    fft_freqs = fftfreq(n, 1/sample_rate)

    # Keep only positive frequencies
    positive_freqs = fft_freqs[:n//2]
    positive_mags = fft_magnitudes[:n//2]

    # Top FFT coefficients (top 5 magnitudes)
    top_indices = np.argsort(positive_mags)[::-1][:5]
    for i, idx in enumerate(top_indices):
        features[f'fft_mag_{i}'] = positive_mags[idx]
        features[f'fft_freq_{i}'] = positive_freqs[idx]

    # Dominant frequency
    features['dominant_freq'] = positive_freqs[np.argmax(positive_mags)]
    features['dominant_mag'] = np.max(positive_mags)

    # Spectral features using periodogram
    freqs, psd = periodogram(rssi_window, fs=sample_rate)

    # Spectral centroid
    features['spectral_centroid'] = np.sum(freqs * psd) / np.sum(psd)

    # Spectral entropy
    psd_norm = psd / np.sum(psd)
    features['spectral_entropy'] = -np.sum(psd_norm * np.log(psd_norm + 1e-10))

    # Band power (5 frequency bands)
    bands = [
        (0, 0.1),   # Very low
        (0.1, 0.2), # Low
        (0.2, 0.3), # Mid-low
        (0.3, 0.4), # Mid-high
        (0.4, 0.5)  # High
    ]
    for i, (low, high) in enumerate(bands):
        mask = (freqs >= low) & (freqs < high)
        features[f'band_power_{i}'] = np.sum(psd[mask])

    # Total power
    features['total_power'] = np.sum(psd)

    # Harmonic distortion
    features['thd'] = np.std(psd) / np.mean(psd)  # Total harmonic distortion

    return features
```

**For 4 detectors:**
- Total frequency-domain features: 15 features × 4 detectors = **60 features**

### 4.3 Correlation Features

**Cross-Detector Correlation:**

```python
from scipy.stats import pearsonr, spearmanr

def compute_correlation_features(all_rssi_windows):
    """
    Compute correlation features between detectors

    Args:
        all_rssi_windows: Dict of {detector_id: RSSI window}

    Returns:
        Dictionary of correlation features
    """
    features = {}
    detectors = list(all_rssi_windows.keys())
    n_detectors = len(detectors)

    # Pairwise correlations
    pearson_corrs = []
    spearman_corrs = []

    for i in range(n_detectors):
        for j in range(i+1, n_detectors):
            det_i = detectors[i]
            det_j = detectors[j]

            # Pearson correlation
            pearson_corr, _ = pearsonr(
                all_rssi_windows[det_i],
                all_rssi_windows[det_j]
            )
            pearson_corrs.append(pearson_corr)
            features[f'pearson_{det_i}_{det_j}'] = pearson_corr

            # Spearman correlation
            spearman_corr, _ = spearmanr(
                all_rssi_windows[det_i],
                all_rssi_windows[det_j]
            )
            spearman_corrs.append(spearman_corr)
            features[f'spearman_{det_i}_{det_j}'] = spearman_corr

    # Aggregate correlation statistics
    features['pearson_mean'] = np.mean(pearson_corrs)
    features['pearson_std'] = np.std(pearson_corrs)
    features['pearson_max'] = np.max(pearson_corrs)
    features['pearson_min'] = np.min(pearson_corrs)

    features['spearman_mean'] = np.mean(spearman_corrs)
    features['spearman_std'] = np.std(spearman_corrs)

    return features
```

**For 4 detectors:**
- Pairwise combinations: 4 choose 2 = 6 pairs
- Correlation features: 6 (Pearson) + 6 (Spearman) + 6 (aggregate) = **18 features**

### 4.4 Temporal Features

**Autocorrelation and Trend:**

```python
def compute_temporal_features(rssi_window):
    """
    Compute temporal features from RSSI window

    Args:
        rssi_window: Array of 20 RSSI values

    Returns:
        Dictionary of temporal features
    """
    features = {}

    # Autocorrelation at different lags
    for lag in [1, 2, 3, 4, 5]:
        autocorr = np.corrcoef(
            rssi_window[:-lag],
            rssi_window[lag:]
        )[0, 1]
        features[f'autocorr_lag_{lag}'] = autocorr

    # Difference between consecutive samples
    diffs = np.diff(rssi_window)
    features['diff_mean'] = np.mean(diffs)
    features['diff_std'] = np.std(diffs)
    features['diff_max'] = np.max(diffs)
    features['diff_min'] = np.min(diffs)

    # Trend coefficient (linear regression slope)
    time_points = np.arange(len(rssi_window))
    slope, intercept = np.polyfit(time_points, rssi_window, 1)
    features['trend_slope'] = slope
    features['trend_intercept'] = intercept

    # Rolling statistics (5-second sub-windows)
    sub_window_size = 5
    rolling_means = []
    rolling_stds = []
    for i in range(0, len(rssi_window) - sub_window_size + 1):
        sub_window = rssi_window[i:i+sub_window_size]
        rolling_means.append(np.mean(sub_window))
        rolling_stds.append(np.std(sub_window))

    features['rolling_mean_mean'] = np.mean(rolling_means)
    features['rolling_mean_std'] = np.std(rolling_means)
    features['rolling_std_mean'] = np.mean(rolling_stds)

    return features
```

**For 4 detectors:**
- Total temporal features: 16 features × 4 detectors = **64 features**

### 4.5 Feature Selection

**Total Feature Count:**
- Time-domain: 48 features
- Frequency-domain: 60 features
- Correlation: 18 features
- Temporal: 64 features
- **Total: 190 features (for 4 detectors)**

**Feature Selection Strategy:**

```python
from sklearn.feature_selection import (
    SelectKBest,
    f_classif,
    mutual_info_classif,
    RFE,
    VarianceThreshold
)
from sklearn.ensemble import RandomForestClassifier

def feature_selection_pipeline(X_train, y_train):
    """
    Perform feature selection in multiple stages

    Args:
        X_train: Feature matrix (n_samples, n_features)
        y_train: Labels

    Returns:
        Selected feature indices
    """
    # Stage 1: Remove low-variance features
    variance_threshold = VarianceThreshold(threshold=0.01)
    X_var = variance_threshold.fit_transform(X_train)
    print(f"After variance threshold: {X_var.shape[1]} features")

    # Stage 2: Select top 100 features using ANOVA F-value
    select_k_best = SelectKBest(score_func=f_classif, k=100)
    X_kbest = select_k_best.fit_transform(X_var, y_train)
    print(f"After SelectKBest: {X_kbest.shape[1]} features")

    # Stage 3: Recursive Feature Elimination (optional, slow)
    # rfe = RFE(
    #     estimator=RandomForestClassifier(n_estimators=50, random_state=42),
    #     n_features_to_select=50,
    #     step=0.1
    # )
    # X_rfe = rfe.fit_transform(X_kbest, y_train)
    # print(f"After RFE: {X_rfe.shape[1]} features")

    # Get selected feature indices
    selected_indices = select_k_best.get_support(indices=True)

    return selected_indices
```

**Feature Importance Ranking:**

```python
# Train Random Forest and extract feature importances
rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_train, y_train)

# Get feature importances
importances = rf.feature_importances_
indices = np.argsort(importances)[::-1]

# Print top 20 features
print("Top 20 Features:")
for i in range(20):
    print(f"{i+1}. {feature_names[indices[i]]} ({importances[indices[i]]:.4f})")
```

**Expected Top Features (Based on Research):**
1. Standard deviation of RSSI (all detectors)
2. Mean RSSI (all detectors)
3. Cross-detector correlation
4. FFT dominant frequency
5. Spectral entropy
6. RSSI variance
7. RSSI skewness
8. Autocorrelation lag 1
9. Rolling statistics
10. Trend slope

**Dimensionality Reduction (Optional):**

```python
# PCA for visualization (not for model training)
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_train_scaled)

print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
# Expected: [0.45, 0.25] = 70% variance explained
```

### 4.6 Real-Time Computation Feasibility

**Computation Time Breakdown (Per 20-second Window):**

| Operation | Time (4 detectors) | Time (8 detectors) | Optimization |
|-----------|-------------------|-------------------|--------------|
| Load raw data | 10ms | 20ms | Cache in memory |
| Time-domain features | 5ms | 10ms | Vectorized operations |
| FFT computation | 15ms | 30ms | Use scipy.fft (fast) |
| Correlation features | 10ms | 40ms | Precompute lookup tables |
| Temporal features | 5ms | 10ms | Vectorized operations |
| Feature scaling | 5ms | 10ms | Pre-fit scaler |
| Model prediction | 50ms | 100ms | Optimized Random Forest |
| **Total** | **100ms** | **220ms** | Well under 1s target |

**Memory Usage:**
- Raw RSSI data: 20 samples × 4 detectors × 4 bytes = 320 bytes
- Feature vector: 100 features × 8 bytes = 800 bytes
- Model in memory: ~20 MB
- **Total: ~20 MB** (acceptable)

**Optimization Techniques:**
1. **Parallelization:** Compute features per detector in parallel
2. **Caching:** Repeatedly used values (e.g., mean, std)
3. **Vectorization:** Use NumPy operations instead of loops
4. **Lazy Computation:** Compute features only when needed
5. **Batch Processing:** Process multiple windows together

---

## 5. Training Data Requirements

### 5.1 Data Collection Strategy

**Data Collection Protocol:**

**Phase 1: Empty Room Calibration (Daily)**
- Duration: 20 minutes
- Conditions: Room completely empty, no movement
- Purpose: Establish noise baseline
- Frequency: Once per day (automatic, nighttime)
- Data: 20 min × 3 windows/min = 60 samples

**Phase 2: Single Person Data (Initial Setup)**
- Stationary: 10 minutes (5 configurations × 2 min each)
  - Sitting at desk
  - Standing still
  - Lying down (if applicable)
  - Different locations in room
- Movement: 10 minutes
  - Walking slowly
  - Walking quickly
  - Random movement
  - Arm movements
- Total: 20 min × 3 windows/min = 60 samples

**Phase 3: Multiple People Data (Initial Setup)**
- For each count (2, 3, 4, 5 people):
  - Stationary: 10 min (5 configs × 2 min)
  - Movement: 10 min (various activities)
  - Edge cases: 5 min (grouped, spread, near/far)
  - Subtotal: 25 min × 3 = 75 samples per count
- Total for 2-5 people: 75 × 4 = 300 samples

**Phase 4: Continuous Data Collection (Ongoing)**
- Passive collection: All detections saved with confidence scores
- Active labeling: Manual verification of 10 random samples/day
- Crowdsourcing: User feedback when detection is wrong
- Target: 100+ new samples per week

**Room Configuration Variations:**
- Different furniture layouts
- Different detector placements
- Different room sizes (test in multiple rooms)
- Different environmental conditions (HVAC on/off, etc.)
- Different times of day

**Data Labeling Process:**
1. **Manual Labeling:** Human operator enters actual count
2. **Video Verification:** Camera records ground truth (optional)
3. **Sensor Fusion:** Use PIR sensors as secondary validation
4. **Crowdsourcing:** Users report incorrect detections
5. **Consensus:** Multiple labelers for ambiguous cases

### 5.2 Data Volume Estimates

**Minimum Viable Dataset (MVP):**
- Presence Detection: 300 samples (150 empty, 150 occupied)
- People Counting: 600 samples (100 per class × 6 classes)
- Total data collection time: ~6 hours
- Storage: 600 samples × 320 bytes = 192 KB (raw data)

**Recommended Production Dataset:**
- Presence Detection: 2000 samples
- People Counting: 5000 samples (balanced)
- Total data collection time: ~40 hours
- Storage: 7000 samples × 320 bytes = 2.2 MB (raw data)

**Ideal Dataset (Long-term):**
- Presence Detection: 10,000+ samples
- People Counting: 20,000+ samples
- Continuous collection: 100+ samples/week
- Storage: 30,000 samples × 320 bytes = 9.6 MB (raw data)

**Data Splitting:**
- Training: 70% (for model training)
- Validation: 15% (for hyperparameter tuning)
- Test: 15% (for final evaluation)

**Cross-Validation:**
- k=3 stratified k-fold (minimum viable)
- k=5 stratified k-fold (recommended)
- k=10 stratified k-fold (ideal, but computationally expensive)

### 5.3 Data Quality Requirements

**Sampling Rate:**
- **Standard:** 1 Hz (1 sample per second per detector)
- **Minimum:** 0.5 Hz (reduced accuracy)
- **Maximum:** 2 Hz (diminishing returns, increased storage)
- **Rationale:** Research shows 1 Hz sufficient for human movement detection

**Label Accuracy Requirements:**
- Primary labeler: >99% accuracy (verified by expert)
- Secondary labeler: >95% accuracy (for consensus)
- Inter-rater reliability: Cohen's kappa >0.8
- Spot-checking: Random 10% verified by expert

**Signal Quality Standards:**
- RSSI Range: -30 to -90 dBm (valid range)
- Out-of-range handling: Exclude samples >20% out-of-range
- Missing data tolerance: <5% per 20-second window
- Signal-to-noise ratio: >10 dB (minimum viable)

**Outlier Handling:**
- Statistical outliers: >3 standard deviations from mean
- Sensor malfunctions: Flatline values (same RSSI for all samples)
- Environmental anomalies: Sudden changes (e.g., detector moved)
- Action: Remove outliers and flag for investigation

**Data Validation Checks:**
```python
def validate_rssi_window(rssi_window):
    """
    Validate RSSI window for quality

    Returns:
        bool: True if valid, False otherwise
    """
    # Check for missing data
    if np.any(np.isnan(rssi_window)) or np.any(np.isinf(rssi_window)):
        return False

    # Check RSSI range
    if np.any(rssi_window > -30) or np.any(rssi_window < -90):
        return False

    # Check for flatline (sensor malfunction)
    if np.std(rssi_window) < 0.1:
        return False

    # Check for outliers (>3 std)
    z_scores = np.abs((rssi_window - np.mean(rssi_window)) / np.std(rssi_window))
    if np.any(z_scores > 3):
        return False

    return True
```

### 5.4 Data Augmentation Techniques

**Noise Injection:**
```python
def add_noise(rssi_window, noise_level=0.5):
    """
    Add Gaussian noise to RSSI window

    Args:
        rssi_window: Original RSSI values
        noise_level: Standard deviation of noise (dB)

    Returns:
        Augmented RSSI window
    """
    noise = np.random.normal(0, noise_level, len(rssi_window))
    return rssi_window + noise
```

**Signal Variation Simulation:**
- Random gain adjustments: ±2 dB
- Time shift: ±1 second
- Amplitude scaling: ±5%
- Baseline drift: ±1 dB over 20 seconds

**Synthetic Data Generation:**
- Mix and match: Combine samples from different classes
- Interpolation: Create intermediate samples between classes
- Generative models: Use GANs to generate synthetic RSSI patterns (advanced)

**Class Balancing:**
- Oversampling: Duplicate minority class samples
- SMOTE: Synthetic Minority Over-sampling Technique
- Undersampling: Reduce majority class samples (not recommended)

**Data Augmentation Pipeline:**
```python
def augment_dataset(X, y, target_samples_per_class=500):
    """
    Augment dataset to balance classes

    Args:
        X: Feature matrix
        y: Labels
        target_samples_per_class: Target samples per class

    Returns:
        Augmented X and y
    """
    from imblearn.over_sampling import SMOTE

    smote = SMOTE(
        sampling_strategy={i: target_samples_per_class for i in np.unique(y)},
        random_state=42
    )
    X_resampled, y_resampled = smote.fit_resample(X, y)

    return X_resampled, y_resampled
```

---

## 6. Model Deployment Strategy

### 6.1 Model Serialization Format

**Options Comparison:**

| Format | Size | Speed | Compatibility | Recommended? |
|--------|------|-------|---------------|--------------|
| **Pickle** | Small | Fast | Python only | ✅ Yes (primary) |
| **Joblib** | Small | Faster | Python only | ✅ Yes (alternative) |
| **ONNX** | Small | Fastest | Cross-platform | ⚠️ Optional |
| **PMML** | Medium | Medium | Java/.NET | ❌ No |
| **HDF5** | Large | Medium | Multi-language | ❌ No |

**Recommended: Python Pickle**

```python
import pickle

# Save model
with open('models/presence_detection_v1.0.pkl', 'wb') as f:
    pickle.dump({
        'model': pipeline,
        'metadata': {
            'version': '1.0',
            'created_at': '2026-02-02',
            'accuracy': 0.992,
            'features': feature_names
        }
    }, f)

# Load model
with open('models/presence_detection_v1.0.pkl', 'rb') as f:
    model_data = pickle.load(f)
    model = model_data['model']
    metadata = model_data['metadata']
```

**Alternative: Joblib (Faster for large models)**

```python
from joblib import dump, load

# Save model
dump(pipeline, 'models/presence_detection_v1.0.joblib')

# Load model
pipeline = load('models/presence_detection_v1.0.joblib')
```

**Optional: ONNX (For cross-platform deployment)**

```python
# Convert sklearn model to ONNX
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

initial_type = [('float_input', FloatTensorType([None, n_features]))]
onnx_model = convert_sklearn(
    pipeline,
    initial_types=initial_type,
    target_opset=12
)

# Save ONNX model
with open('models/presence_detection_v1.0.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())
```

### 6.2 Model Versioning and A/B Testing

**Version Numbering: Semantic Versioning**
- Major version (X.0.0): Breaking changes (e.g., new feature set)
- Minor version (1.X.0): New features (e.g., extended to 9 classes)
- Patch version (1.0.X): Bug fixes, retraining

**Version History:**

```
models/
├── presence/
│   ├── v1.0.0.pkl (Initial release)
│   ├── v1.0.1.pkl (Bug fix: recalibration issue)
│   ├── v1.1.0.pkl (New feature: skewness)
│   └── v2.0.0.pkl (Breaking change: new algorithm)
└── counting/
    ├── v1.0.0.pkl (Initial: 4 detectors, 0-5 classes)
    ├── v1.1.0.pkl (Extended: 0-9 classes)
    └── v2.0.0.pkl (Optimized: feature selection)
```

**A/B Testing Framework:**

```python
class ModelABTest:
    def __init__(self, model_a_path, model_b_path, traffic_split=0.1):
        """
        Initialize A/B test

        Args:
            model_a_path: Path to baseline model
            model_b_path: Path to new model
            traffic_split: Fraction of traffic to model B (0.1 = 10%)
        """
        self.model_a = load(model_a_path)
        self.model_b = load(model_b_path)
        self.traffic_split = traffic_split

        # Metrics tracking
        self.metrics_a = {'correct': 0, 'total': 0}
        self.metrics_b = {'correct': 0, 'total': 0}

    def predict(self, X, true_label=None):
        """
        Route prediction to model A or B

        Args:
            X: Features
            true_label: Ground truth (for evaluation)

        Returns:
            Prediction from selected model
        """
        # Route to model B based on traffic split
        if np.random.random() < self.traffic_split:
            pred = self.model_b.predict(X)[0]

            # Track metrics if ground truth available
            if true_label is not None:
                self.metrics_b['total'] += 1
                if pred == true_label:
                    self.metrics_b['correct'] += 1
        else:
            pred = self.model_a.predict(X)[0]

            if true_label is not None:
                self.metrics_a['total'] += 1
                if pred == true_label:
                    self.metrics_a['correct'] += 1

        return pred

    def get_results(self):
        """Get A/B test results"""
        acc_a = self.metrics_a['correct'] / max(self.metrics_a['total'], 1)
        acc_b = self.metrics_b['correct'] / max(self.metrics_b['total'], 1)

        return {
            'model_a_accuracy': acc_a,
            'model_b_accuracy': acc_b,
            'model_a_samples': self.metrics_a['total'],
            'model_b_samples': self.metrics_b['total']
        }
```

**Rollback Decision Criteria:**
- If model B accuracy < model A accuracy - 1%: Rollback
- If model B latency > model A latency + 50%: Rollback
- If model B error rate > 5%: Immediate rollback
- If user complaints > 10/day: Investigate and possibly rollback

### 6.3 Performance Monitoring

**Metrics to Track:**

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| **Accuracy** | Correct predictions / Total | >98% (counting), >99% (presence) | <95% |
| **Latency (p50)** | Median response time | <100ms | >500ms |
| **Latency (p95)** | 95th percentile response time | <500ms | >2000ms |
| **Latency (p99)** | 99th percentile response time | <1000ms | >5000ms |
| **Error Rate** | Failed predictions / Total | <1% | >5% |
| **Resource Usage** | CPU, Memory utilization | <70% CPU, <1GB RAM | >90% CPU, >2GB RAM |
| **Data Drift** | Feature distribution change | <5% | >10% |

**Monitoring Implementation:**

```python
import time
import psutil
import numpy as np

class ModelMonitor:
    def __init__(self, model_name):
        self.model_name = model_name
        self.predictions = []
        self.latencies = []
        self.accuracies = []
        self.process = psutil.Process()

    def predict(self, model, X, true_label=None):
        """
        Make prediction and track metrics

        Args:
            model: Model to use
            X: Features
            true_label: Ground truth (optional)

        Returns:
            Prediction
        """
        # Track latency
        start_time = time.time()
        pred = model.predict(X)[0]
        latency = (time.time() - start_time) * 1000  # ms
        self.latencies.append(latency)

        # Track accuracy if ground truth available
        if true_label is not None:
            correct = int(pred == true_label)
            self.predictions.append(correct)

            # Calculate rolling accuracy (last 100 predictions)
            if len(self.predictions) >= 100:
                recent_accuracy = np.mean(self.predictions[-100:])
                self.accuracies.append(recent_accuracy)

                # Alert if accuracy drops
                if recent_accuracy < 0.95:
                    print(f"⚠️ LOW ACCURACY ALERT: {recent_accuracy:.3f}")

        # Track resource usage
        cpu_percent = self.process.cpu_percent()
        memory_mb = self.process.memory_info().rss / 1024 / 1024

        # Alert if resource usage high
        if cpu_percent > 90:
            print(f"⚠️ HIGH CPU ALERT: {cpu_percent:.1f}%")
        if memory_mb > 2000:
            print(f"⚠️ HIGH MEMORY ALERT: {memory_mb:.1f} MB")

        return pred

    def get_metrics(self):
        """Get current metrics"""
        return {
            'latency_p50': np.percentile(self.latencies, 50),
            'latency_p95': np.percentile(self.latencies, 95),
            'latency_p99': np.percentile(self.latencies, 99),
            'accuracy': np.mean(self.accuracies) if self.accuracies else None,
            'cpu_percent': self.process.cpu_percent(),
            'memory_mb': self.process.memory_info().rss / 1024 / 1024
        }
```

**Data Drift Detection:**

```python
from scipy.stats import ks_2samp

def detect_data_drift(new_features, reference_features, threshold=0.05):
    """
    Detect if feature distribution has changed

    Args:
        new_features: Recent feature values
        reference_features: Baseline feature values (from training)
        threshold: P-value threshold for drift detection

    Returns:
        bool: True if drift detected
    """
    # Kolmogorov-Smirnov test for each feature
    drift_detected = False

    for i in range(new_features.shape[1]):
        ks_statistic, p_value = ks_2samp(
            new_features[:, i],
            reference_features[:, i]
        )

        if p_value < threshold:
            print(f"⚠️ DATA DRIFT DETECTED in feature {i}: p-value={p_value:.4f}")
            drift_detected = True

    return drift_detected
```

### 6.4 Retraining Triggers

**Trigger Types:**

**1. Scheduled Retraining:**
- **Frequency:** Weekly (automatic)
- **Time:** Sunday 2 AM (low traffic)
- **Data:** All data since last retraining
- **Validation:** Compare new model vs. current model
- **Deployment:** Automatic if accuracy improves >0.5%

**2. Performance-Based Retraining:**
- **Trigger:** Accuracy drops below 95% for 24 hours
- **Action:** Immediate investigation + retraining
- **Data:** Recent data (last 7 days) + baseline data
- **Deployment:** Manual review required

**3. Data-Based Retraining:**
- **Trigger:** 500+ new samples collected
- **Action:** Next scheduled retraining
- **Data:** New samples + 50% old samples (refresh)
- **Deployment:** Automatic if validation passes

**4. Drift-Based Retraining:**
- **Trigger:** Feature distribution change >10%
- **Action:** Investigate drift source + retrain
- **Data:** New distribution samples + adjusted baseline
- **Deployment:** Manual review required

**Retraining Pipeline:**

```python
def retrain_model(model_type='counting'):
    """
    Retrain model with latest data

    Args:
        model_type: 'presence' or 'counting'

    Returns:
        New model accuracy and deployment recommendation
    """
    # Load latest data
    X_train, y_train = load_training_data(model_type)
    X_val, y_val = load_validation_data(model_type)

    # Train new model
    new_model = train_model(X_train, y_train, model_type)

    # Evaluate
    new_accuracy = new_model.score(X_val, y_val)
    print(f"New model accuracy: {new_accuracy:.3f}")

    # Load current model
    current_model = load_current_model(model_type)
    current_accuracy = current_model.score(X_val, y_val)
    print(f"Current model accuracy: {current_accuracy:.3f}")

    # Compare
    accuracy_improvement = new_accuracy - current_accuracy

    # Deployment decision
    if accuracy_improvement > 0.01:  # 1% improvement
        deploy = True
        reason = f"Accuracy improved by {accuracy_improvement:.1%}"
    elif accuracy_improvement > -0.01:  # Within 1%
        deploy = False
        reason = "Accuracy similar to current model"
    else:  # Degraded
        deploy = False
        reason = f"Accuracy degraded by {-accuracy_improvement:.1%}"

    # Save new model if better
    if deploy:
        save_model(new_model, model_type)

    return {
        'new_accuracy': new_accuracy,
        'current_accuracy': current_accuracy,
        'improvement': accuracy_improvement,
        'deploy': deploy,
        'reason': reason
    }
```

### 6.5 Edge Deployment Considerations

**Model Size Optimization:**

| Technique | Size Reduction | Accuracy Impact | Recommended? |
|-----------|----------------|-----------------|--------------|
| **Feature Selection** | 50% reduction | None (if done correctly) | ✅ Yes |
| **Model Pruning** | 30% reduction | <0.5% | ⚠️ Optional |
| **Quantization (int8)** | 75% reduction | <0.1% | ✅ Yes |
| **Knowledge Distillation** | 50% reduction | <1% | ⚠️ Optional |
| **ONNX Optimization** | 20% reduction | None | ✅ Yes |

**Quantization Example:**

```python
# Convert float32 model to int8 (4x size reduction)
from sklearn.ensemble import RandomForestClassifier
import onnx
from onnxruntime.quantization import quantize_dynamic

# Convert to ONNX first
onnx_model = convert_sklearn(pipeline, initial_types=initial_type)

# Quantize to int8
quantized_model = 'models/presence_detection_v1.0.quant.onnx'
quantize_dynamic(
    model_input='models/presence_detection_v1.0.onnx',
    model_output=quantized_model,
    weight_type=QuantType.QInt8
)
```

**Hardware Acceleration:**

| Hardware | Speedup | Cost | Power | Recommended? |
|----------|---------|------|-------|--------------|
| **CPU (Base)** | 1x | Low | Low | ✅ Baseline |
| **GPU (NVIDIA)** | 10x | High | High | ❌ Overkill |
| **NPU (Intel/ARM)** | 5x | Medium | Low | ⚠️ Optional |
| **TPU (Google)** | 20x | High | Medium | ❌ Overkill |
| **FPGA** | 15x | Very High | Medium | ❌ Complex |

**Recommended:** CPU-only deployment (sufficient for <500ms inference)

**Edge Device Specifications:**

**Minimum Requirements:**
- CPU: ARM Cortex-A53 or Intel Atom (1 GHz+)
- RAM: 512 MB
- Storage: 100 MB
- OS: Linux (any distro) or Windows IoT

**Recommended Requirements:**
- CPU: ARM Cortex-A72 or Intel Core i3 (2 GHz+)
- RAM: 2 GB
- Storage: 1 GB
- OS: Ubuntu 20.04 LTS or Raspberry Pi OS

**Deployment Options:**

1. **Docker Container (Recommended):**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY models/ /app/models/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "server.py"]
```

2. **Systemd Service (Linux):**
```ini
[Unit]
Description=WiFi People Detection Service
After=network.target

[Service]
Type=simple
User=detection
WorkingDirectory=/opt/detection
ExecStart=/usr/bin/python3 /opt/detection/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Binary Executable (PyInstaller):**
```bash
# Convert Python script to standalone executable
pyinstaller --onefile --name detection-service server.py
```

---

## 7. Model Evaluation Framework

### 7.1 Cross-Validation Strategy

**Stratified K-Fold Cross-Validation:**

```python
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def cross_validate_model(X, y, model, n_splits=5):
    """
    Perform stratified k-fold cross-validation

    Args:
        X: Feature matrix
        y: Labels
        model: Model to evaluate
        n_splits: Number of folds

    Returns:
        Dictionary of evaluation metrics
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    accuracies = []
    precisions = []
    recalls = []
    f1_scores = []

    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        print(f"\n{'='*50}")
        print(f"Fold {fold + 1}/{n_splits}")
        print(f"{'='*50}")

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Train model
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_val)

        # Metrics
        accuracy = accuracy_score(y_val, y_pred)
        accuracies.append(accuracy)

        print(f"Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_val, y_pred))

        print("\nConfusion Matrix:")
        print(confusion_matrix(y_val, y_pred))

    # Aggregate results
    results = {
        'mean_accuracy': np.mean(accuracies),
        'std_accuracy': np.std(accuracies),
        'accuracies': accuracies
    }

    print(f"\n{'='*50}")
    print("Cross-Validation Results")
    print(f"{'='*50}")
    print(f"Mean Accuracy: {results['mean_accuracy']:.3f} (+/- {results['std_accuracy']:.3f})")

    return results
```

**Cross-Validation Results (Expected):**

| Model | Mean Accuracy | Std Accuracy | Min Accuracy | Max Accuracy |
|-------|---------------|--------------|--------------|--------------|
| Presence Detection | 0.992 | 0.008 | 0.981 | 0.998 |
| People Counting (4 det) | 0.985 | 0.012 | 0.968 | 0.997 |

### 7.2 Test Set Composition

**Test Set Requirements:**

**Stratified Sampling:**
- Balanced classes: Equal representation of 0, 1, 2, 3, 4, 5 people
- Size: 15% of total dataset
- Unseen data: Not used in training or validation

**Temporal Split (Optional):**
- Train: First 70% of data (chronologically)
- Validation: Next 15%
- Test: Last 15%
- Rationale: Simulates real-world deployment on future data

**Room-Based Split (Optional):**
- Train: Rooms A, B, C
- Validation: Room D
- Test: Room E
- Rationale: Tests generalization to new environments

**Final Test Set Evaluation:**

```python
def final_evaluation(model, X_test, y_test, model_name):
    """
    Final evaluation on test set

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        model_name: Name of model
    """
    # Predict
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'='*50}")
    print(f"Final Test Set Evaluation: {model_name}")
    print(f"{'='*50}")
    print(f"Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(report)
    print("\nConfusion Matrix:")
    print(cm)

    # Per-class metrics
    classes = np.unique(y_test)
    for cls in classes:
        true_positives = np.sum((y_test == cls) & (y_pred == cls))
        false_positives = np.sum((y_test != cls) & (y_pred == cls))
        false_negatives = np.sum((y_test == cls) & (y_pred != cls))

        precision = true_positives / (true_positives + false_positives)
        recall = true_positives / (true_positives + false_negatives)
        f1 = 2 * (precision * recall) / (precision + recall)

        print(f"\nClass {cls}:")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall: {recall:.3f}")
        print(f"  F1 Score: {f1:.3f}")
```

### 7.3 Performance Baseline Establishment

**Baseline Models:**

| Model | Description | Expected Accuracy | Use Case |
|-------|-------------|-------------------|----------|
| **Random Guess** | Uniform random selection | 16.7% (6 classes) | Sanity check |
| **Majority Class** | Always predict most common class | 16.7% | Baseline |
| **Threshold (Presence)** | Std dev threshold | 90% | Simple baseline |
| **Logistic Regression** | Linear classifier | 92% | Linear baseline |
| **k-NN (k=5)** | Nearest neighbors | 94% | Non-linear baseline |
| **Decision Tree** | Single tree | 95% | Tree baseline |
| **Random Forest** | Ensemble of trees | 98.5% | ✅ Target model |

**Baseline Comparison:**

```python
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

def compare_baselines(X_train, y_train, X_test, y_test):
    """
    Compare multiple baseline models

    Returns:
        DataFrame of results
    """
    models = {
        'Random Guess': DummyClassifier(strategy='uniform'),
        'Majority Class': DummyClassifier(strategy='most_frequent'),
        'Logistic Regression': LogisticRegression(max_iter=1000),
        'k-NN (k=5)': KNeighborsClassifier(n_neighbors=5),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42)
    }

    results = []

    for name, model in models.items():
        model.fit(X_train, y_train)
        accuracy = model.score(X_test, y_test)
        results.append({'Model': name, 'Accuracy': accuracy})

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Accuracy', ascending=False)

    print("\nBaseline Comparison:")
    print(results_df.to_string(index=False))

    return results_df
```

**Expected Output:**

```
Baseline Comparison:
               Model  Accuracy
       Random Forest    0.9850
        Decision Tree    0.9520
            k-NN (k=5)    0.9410
  Logistic Regression    0.9230
      Majority Class    0.1670
        Random Guess    0.1650
```

### 7.4 Continuous Evaluation Pipeline

**Automated Evaluation Pipeline:**

```python
import schedule
import time

def continuous_evaluation_pipeline():
    """
    Run evaluation pipeline every week
    """
    # Load latest data
    X_new, y_new = load_latest_data()

    # Load current model
    model = load_current_model()

    # Evaluate
    accuracy = model.score(X_new, y_new)

    print(f"Current model accuracy on new data: {accuracy:.3f}")

    # Check if retraining needed
    if accuracy < 0.95:
        print("⚠️ Accuracy below threshold, triggering retraining...")
        retrain_model()

    # Log results
    log_evaluation_results(accuracy, model.version)

# Schedule weekly evaluation
schedule.every().sunday.at("02:00").do(continuous_evaluation_pipeline)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

**Model Comparison Metrics:**

```python
def compare_models(models_dict, X_test, y_test):
    """
    Compare multiple models on test set

    Args:
        models_dict: Dictionary of {model_name: model}
        X_test: Test features
        y_test: Test labels

    Returns:
        DataFrame of comparison
    """
    results = []

    for name, model in models_dict.items():
        # Predict
        y_pred = model.predict(X_test)

        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')

        # Latency
        start_time = time.time()
        model.predict(X_test[:1])
        latency = (time.time() - start_time) * 1000  # ms

        results.append({
            'Model': name,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1 Score': f1,
            'Latency (ms)': latency
        })

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Accuracy', ascending=False)

    print("\nModel Comparison:")
    print(results_df.to_string(index=False))

    return results_df
```

**Evaluation Dashboard (Web UI):**

- Real-time accuracy display
- Confusion matrix visualization
- Per-class performance trends
- Latency percentiles (p50, p95, p99)
- Resource utilization charts
- Model version history
- A/B test results

---

## Appendix A: Feature Engineering Code Samples

```python
# Complete feature extraction pipeline
import numpy as np
from scipy import stats
from scipy.fft import fft
from scipy.stats import pearsonr

def extract_all_features(rssi_data_dict):
    """
    Extract all features from RSSI data

    Args:
        rssi_data_dict: Dictionary of {detector_id: RSSI window (20 samples)}

    Returns:
        Feature vector (numpy array)
    """
    all_features = []

    # Time-domain features
    for detector_id, rssi_window in rssi_data_dict.items():
        time_features = compute_time_domain_features(rssi_window)
        all_features.extend(list(time_features.values()))

    # Frequency-domain features
    for detector_id, rssi_window in rssi_data_dict.items():
        freq_features = compute_frequency_domain_features(rssi_window)
        all_features.extend(list(freq_features.values()))

    # Correlation features
    corr_features = compute_correlation_features(rssi_data_dict)
    all_features.extend(list(corr_features.values()))

    # Temporal features
    for detector_id, rssi_window in rssi_data_dict.items():
        temp_features = compute_temporal_features(rssi_window)
        all_features.extend(list(temp_features.values()))

    return np.array(all_features)
```

## Appendix B: Model Training Script

```python
#!/usr/bin/env python3
"""
Train WiFi People Detection Models
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import joblib

def load_data(data_path):
    """Load training data from CSV"""
    df = pd.read_csv(data_path)

    # Separate features and labels
    X = df.drop(['label'], axis=1).values
    y = df['label'].values

    return X, y

def train_presence_detection(X, y):
    """Train presence detection model"""
    print("\n" + "="*50)
    print("Training Presence Detection Model")
    print("="*50)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Create pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(
            C=1.0,
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        ))
    ])

    # Train
    pipeline.fit(X_train, y_train)

    # Evaluate
    accuracy = pipeline.score(X_test, y_test)
    print(f"\nTest Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred))

    # Cross-validation
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5)
    print(f"\nCross-Validation Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    return pipeline

def train_people_counting(X, y):
    """Train people counting model"""
    print("\n" + "="*50)
    print("Training People Counting Model")
    print("="*50)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Create pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    # Train
    pipeline.fit(X_train, y_train)

    # Evaluate
    accuracy = pipeline.score(X_test, y_test)
    print(f"\nTest Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred))

    # Cross-validation
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=3)
    print(f"\nCross-Validation Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    # Feature importances
    feature_importances = pipeline.named_steps['classifier'].feature_importances_
    top_indices = np.argsort(feature_importances)[::-1][:10]
    print("\nTop 10 Features:")
    for i, idx in enumerate(top_indices):
        print(f"{i+1}. Feature {idx}: {feature_importances[idx]:.4f}")

    return pipeline

def main():
    """Main training pipeline"""
    print("\n" + "="*50)
    print("WiFi People Detection - Model Training")
    print("="*50)

    # Load presence detection data
    print("\nLoading presence detection data...")
    X_presence, y_presence = load_data('data/presence_detection.csv')
    presence_model = train_presence_detection(X_presence, y_presence)

    # Save presence model
    joblib.dump(presence_model, 'models/presence_detection_v1.0.pkl')
    print("\n✓ Presence detection model saved to models/presence_detection_v1.0.pkl")

    # Load people counting data
    print("\nLoading people counting data...")
    X_counting, y_counting = load_data('data/people_counting.csv')
    counting_model = train_people_counting(X_counting, y_counting)

    # Save counting model
    joblib.dump(counting_model, 'models/people_counting_v1.0.pkl')
    print("\n✓ People counting model saved to models/people_counting_v1.0.pkl")

    print("\n" + "="*50)
    print("Training Complete!")
    print("="*50)

if __name__ == '__main__':
    main()
```

---

**Document End**
**Next Steps:**
1. Review and approve ML/AI requirements
2. Proceed to security and privacy documentation
3. Implement feature engineering pipeline
4. Begin initial model training with collected data
