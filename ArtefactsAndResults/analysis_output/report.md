# Evaluation Analysis Report

_Generated: 2026-05-25_

## Dataset Overview

| Property | Value |
| :--- | :--- |
| Models | google/gemini-3-flash-preview, mistralai/mistral-large-2512, mistralai/mistral-small-2603 |
| Approaches | agentic_rag, crag, lightrag |
| Metrics | answer_relevancy, context_precision, context_recall, context_relevancy, faithfulness, legal_interpretability, regulatory_grounding |
| Unique questions | 153 |
| Scored rows (question × metric) | 9324 |

### Question Count per Model × Approach

| model | approach | unique_questions |
| :--- | :--- | :--- |
| google/gemini-3-flash-preview | agentic_rag | 153 |
| google/gemini-3-flash-preview | crag | 153 |
| google/gemini-3-flash-preview | lightrag | 153 |
| mistralai/mistral-large-2512 | agentic_rag | 153 |
| mistralai/mistral-large-2512 | crag | 153 |
| mistralai/mistral-large-2512 | lightrag | 153 |
| mistralai/mistral-small-2603 | agentic_rag | 153 |
| mistralai/mistral-small-2603 | crag | 153 |
| mistralai/mistral-small-2603 | lightrag | 153 |

## Score Summaries

> Values: **mean ± 95 % CI (n = number of scored question–metric pairs)**.

### Avg score

#### By Model

| metric | google/gemini-3-flash-preview | mistralai/mistral-large-2512 | mistralai/mistral-small-2603 |
| :--- | :--- | :--- | :--- |
| answer_relevancy | 0.774 ± 0.018 (n=459) | 0.783 ± 0.018 (n=459) | 0.770 ± 0.018 (n=458) |
| context_precision | 0.543 ± 0.036 (n=437) | 0.550 ± 0.035 (n=440) | 0.525 ± 0.036 (n=440) |
| context_recall | 0.544 ± 0.040 (n=457) | 0.556 ± 0.040 (n=455) | 0.535 ± 0.040 (n=456) |
| context_relevancy | 0.418 ± 0.031 (n=375) | 0.454 ± 0.028 (n=400) | 0.395 ± 0.027 (n=428) |
| faithfulness | 0.985 ± 0.005 (n=433) | 0.980 ± 0.005 (n=432) | 0.978 ± 0.005 (n=441) |
| legal_interpretability | 0.974 ± 0.011 (n=459) | 0.960 ± 0.012 (n=459) | 0.961 ± 0.014 (n=459) |
| regulatory_grounding | 0.734 ± 0.028 (n=459) | 0.817 ± 0.028 (n=459) | 0.771 ± 0.029 (n=459) |

#### By Approach

| metric | agentic_rag | crag | lightrag |
| :--- | :--- | :--- | :--- |
| answer_relevancy | 0.793 ± 0.017 (n=459) | 0.782 ± 0.017 (n=459) | 0.751 ± 0.020 (n=458) |
| context_precision | 0.501 ± 0.038 (n=459) | 0.580 ± 0.032 (n=457) | 0.536 ± 0.037 (n=401) |
| context_recall | 0.423 ± 0.039 (n=458) | 0.549 ± 0.039 (n=459) | 0.666 ± 0.038 (n=451) |
| context_relevancy | 0.322 ± 0.028 (n=459) | 0.504 ± 0.028 (n=459) | 0.448 ± 0.024 (n=285) |
| faithfulness | 0.971 ± 0.007 (n=394) | 0.979 ± 0.005 (n=459) | 0.993 ± 0.003 (n=453) |
| legal_interpretability | 0.966 ± 0.010 (n=459) | 0.959 ± 0.014 (n=459) | 0.970 ± 0.012 (n=459) |
| regulatory_grounding | 0.863 ± 0.026 (n=459) | 0.695 ± 0.025 (n=459) | 0.765 ± 0.032 (n=459) |

#### By Model × Approach (all metrics pooled)

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.6959 | 0.0232 | 1045 |
| google/gemini-3-flash-preview \| crag | 0.7072 | 0.0202 | 1069 |
| google/gemini-3-flash-preview \| lightrag | 0.7515 | 0.0206 | 965 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.6700 | 0.0237 | 1046 |
| mistralai/mistral-large-2512 \| crag | 0.7656 | 0.0175 | 1071 |
| mistralai/mistral-large-2512 \| lightrag | 0.7641 | 0.0207 | 987 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.6904 | 0.0224 | 1056 |
| mistralai/mistral-small-2603 \| crag | 0.6908 | 0.0209 | 1071 |
| mistralai/mistral-small-2603 \| lightrag | 0.7435 | 0.0211 | 1014 |

### Pass rate

#### By Model

| metric | google/gemini-3-flash-preview | mistralai/mistral-large-2512 | mistralai/mistral-small-2603 |
| :--- | :--- | :--- | :--- |
| answer_relevancy | 0.708 ± 0.042 (n=459) | 0.715 ± 0.041 (n=459) | 0.712 ± 0.042 (n=458) |
| context_precision | 0.460 ± 0.047 (n=437) | 0.434 ± 0.046 (n=440) | 0.441 ± 0.047 (n=440) |
| context_recall | 0.470 ± 0.046 (n=457) | 0.473 ± 0.046 (n=455) | 0.463 ± 0.046 (n=456) |
| context_relevancy | 0.221 ± 0.042 (n=375) | 0.212 ± 0.040 (n=400) | 0.161 ± 0.035 (n=428) |
| faithfulness | 0.998 ± 0.005 (n=433) | 0.993 ± 0.008 (n=432) | 0.991 ± 0.009 (n=441) |
| legal_interpretability | 0.959 ± 0.018 (n=459) | 0.967 ± 0.016 (n=459) | 0.959 ± 0.018 (n=459) |
| regulatory_grounding | 0.547 ± 0.046 (n=459) | 0.728 ± 0.041 (n=459) | 0.651 ± 0.044 (n=459) |

#### By Approach

| metric | agentic_rag | crag | lightrag |
| :--- | :--- | :--- | :--- |
| answer_relevancy | 0.736 ± 0.040 (n=459) | 0.734 ± 0.041 (n=459) | 0.664 ± 0.043 (n=458) |
| context_precision | 0.429 ± 0.045 (n=459) | 0.451 ± 0.046 (n=457) | 0.456 ± 0.049 (n=401) |
| context_recall | 0.338 ± 0.043 (n=458) | 0.466 ± 0.046 (n=459) | 0.603 ± 0.045 (n=451) |
| context_relevancy | 0.155 ± 0.033 (n=459) | 0.320 ± 0.043 (n=459) | 0.067 ± 0.029 (n=285) |
| faithfulness | 0.985 ± 0.012 (n=394) | 0.996 ± 0.006 (n=459) | 1.000 ± 0.000 (n=453) |
| legal_interpretability | 0.976 ± 0.014 (n=459) | 0.952 ± 0.020 (n=459) | 0.956 ± 0.019 (n=459) |
| regulatory_grounding | 0.810 ± 0.036 (n=459) | 0.449 ± 0.046 (n=459) | 0.667 ± 0.043 (n=459) |

#### By Model × Approach (all metrics pooled)

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.6402 | 0.0291 | 1045 |
| google/gemini-3-flash-preview \| crag | 0.6043 | 0.0294 | 1069 |
| google/gemini-3-flash-preview \| lightrag | 0.6549 | 0.0300 | 965 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.6119 | 0.0296 | 1046 |
| mistralai/mistral-large-2512 \| crag | 0.6667 | 0.0283 | 1071 |
| mistralai/mistral-large-2512 \| lightrag | 0.6809 | 0.0291 | 987 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.6250 | 0.0292 | 1056 |
| mistralai/mistral-small-2603 \| crag | 0.6013 | 0.0294 | 1071 |
| mistralai/mistral-small-2603 \| lightrag | 0.6627 | 0.0291 | 1014 |

## Per-Metric Results

### answer_relevancy

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.8065 | 0.0250 | 153 |
| google/gemini-3-flash-preview \| crag | 0.7729 | 0.0337 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.7425 | 0.0344 | 153 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.7948 | 0.0326 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.7949 | 0.0269 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.7593 | 0.0347 | 153 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.7784 | 0.0298 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.7790 | 0.0258 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.7512 | 0.0366 | 152 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.7712 | 0.0673 | 153 |
| google/gemini-3-flash-preview \| crag | 0.7124 | 0.0725 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.6405 | 0.0769 | 153 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.7255 | 0.0715 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.7386 | 0.0704 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.6797 | 0.0748 | 153 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.7124 | 0.0725 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.7516 | 0.0692 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.6711 | 0.0755 | 152 |

### context_precision

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.5060 | 0.0653 | 153 |
| google/gemini-3-flash-preview \| crag | 0.5562 | 0.0596 | 151 |
| google/gemini-3-flash-preview \| lightrag | 0.5702 | 0.0649 | 133 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.4666 | 0.0664 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.6455 | 0.0496 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.5354 | 0.0640 | 134 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.5291 | 0.0644 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.5389 | 0.0577 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.5033 | 0.0658 | 134 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.4379 | 0.0795 | 153 |
| google/gemini-3-flash-preview \| crag | 0.4570 | 0.0804 | 151 |
| google/gemini-3-flash-preview \| lightrag | 0.4887 | 0.0861 | 133 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.3922 | 0.0782 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.4706 | 0.0800 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.4403 | 0.0851 | 134 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.4575 | 0.0798 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.4248 | 0.0792 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.4403 | 0.0851 | 134 |

### context_recall

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.4326 | 0.0686 | 152 |
| google/gemini-3-flash-preview \| crag | 0.5291 | 0.0684 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.6713 | 0.0662 | 152 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.3823 | 0.0675 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.6216 | 0.0648 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.6672 | 0.0669 | 149 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.4529 | 0.0680 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.4950 | 0.0684 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.6599 | 0.0677 | 150 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.3487 | 0.0766 | 152 |
| google/gemini-3-flash-preview \| crag | 0.4510 | 0.0797 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.6118 | 0.0784 | 152 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.3007 | 0.0735 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.5294 | 0.0800 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.5906 | 0.0799 | 149 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.3660 | 0.0772 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.4183 | 0.0790 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.6067 | 0.0791 | 150 |

### context_relevancy

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.3112 | 0.0487 | 153 |
| google/gemini-3-flash-preview \| crag | 0.4924 | 0.0514 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.4884 | 0.0464 | 69 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.3115 | 0.0483 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.5938 | 0.0403 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.4568 | 0.0402 | 94 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.3432 | 0.0475 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.4272 | 0.0497 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.4193 | 0.0396 | 122 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.1569 | 0.0583 | 153 |
| google/gemini-3-flash-preview \| crag | 0.3529 | 0.0766 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.0725 | 0.0627 | 69 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.1503 | 0.0573 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.3725 | 0.0775 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.0532 | 0.0462 | 94 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.1569 | 0.0583 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.2353 | 0.0680 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.0738 | 0.0470 | 122 |

### faithfulness

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.9728 | 0.0127 | 128 |
| google/gemini-3-flash-preview \| crag | 0.9883 | 0.0065 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.9917 | 0.0052 | 152 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.9770 | 0.0123 | 128 |
| mistralai/mistral-large-2512 \| crag | 0.9696 | 0.0101 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.9933 | 0.0046 | 151 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.9633 | 0.0129 | 138 |
| mistralai/mistral-small-2603 \| crag | 0.9777 | 0.0081 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.9929 | 0.0039 | 150 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.9922 | 0.0155 | 128 |
| google/gemini-3-flash-preview \| crag | 1.0000 | 0.0000 | 153 |
| google/gemini-3-flash-preview \| lightrag | 1.0000 | 0.0000 | 152 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.9844 | 0.0218 | 128 |
| mistralai/mistral-large-2512 \| crag | 0.9935 | 0.0129 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 1.0000 | 0.0000 | 151 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.9783 | 0.0246 | 138 |
| mistralai/mistral-small-2603 \| crag | 0.9935 | 0.0129 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 1.0000 | 0.0000 | 150 |

### legal_interpretability

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.9954 | 0.0090 | 153 |
| google/gemini-3-flash-preview \| crag | 0.9758 | 0.0175 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.9503 | 0.0268 | 153 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.9399 | 0.0203 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.9582 | 0.0233 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.9824 | 0.0172 | 153 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.9614 | 0.0186 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.9418 | 0.0319 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.9784 | 0.0173 | 153 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.9935 | 0.0129 | 153 |
| google/gemini-3-flash-preview \| crag | 0.9542 | 0.0335 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.9281 | 0.0414 | 153 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.9608 | 0.0311 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.9673 | 0.0285 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.9739 | 0.0256 | 153 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.9739 | 0.0256 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.9346 | 0.0396 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.9673 | 0.0285 | 153 |

### regulatory_grounding

#### Avg score

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.8902 | 0.0408 | 153 |
| google/gemini-3-flash-preview \| crag | 0.6333 | 0.0376 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.6791 | 0.0550 | 153 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.8680 | 0.0453 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.7758 | 0.0432 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.8078 | 0.0561 | 153 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.8314 | 0.0486 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.6758 | 0.0482 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.8072 | 0.0529 | 153 |

#### Pass rate

| model_approach | mean | ± CI (95%) | n |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.8366 | 0.0592 | 153 |
| google/gemini-3-flash-preview \| crag | 0.3007 | 0.0735 | 153 |
| google/gemini-3-flash-preview \| lightrag | 0.5033 | 0.0801 | 153 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.8301 | 0.0602 | 153 |
| mistralai/mistral-large-2512 \| crag | 0.5948 | 0.0787 | 153 |
| mistralai/mistral-large-2512 \| lightrag | 0.7582 | 0.0686 | 153 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.7647 | 0.0680 | 153 |
| mistralai/mistral-small-2603 \| crag | 0.4510 | 0.0797 | 153 |
| mistralai/mistral-small-2603 \| lightrag | 0.7386 | 0.0704 | 153 |

## Cost Analysis

### Token Usage and Raw Cost

| model | approach | input_tokens | output_tokens | cost_usd | used_estimate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| mistralai/mistral-small-2603 | agentic_rag | 4620098 | 480841 | 0.9815 | actual |
| mistralai/mistral-large-2512 | agentic_rag | 3170219 | 627402 | 2.5262 | actual |
| google/gemini-3-flash-preview | agentic_rag | 4213270 | 340742 | 3.1289 | actual |
| mistralai/mistral-small-2603 | crag | 2353556 | 787395 | 0.8255 | actual |
| mistralai/mistral-large-2512 | crag | 2346004 | 931394 | 2.5701 | actual |
| google/gemini-3-flash-preview | crag | 2357934 | 678060 | 3.2131 | actual |
| mistralai/mistral-small-2603 | lightrag | 2722707 | 238804 | 0.5517 | actual |
| mistralai/mistral-large-2512 | lightrag | 2704934 | 257950 | 1.7394 | actual |
| google/gemini-3-flash-preview | lightrag | 2698883 | 118720 | 1.7056 | actual |

### Score per Dollar

| model_approach | avg_score | cost (USD) | score / USD |
| :--- | :--- | :--- | :--- |
| google/gemini-3-flash-preview \| agentic_rag | 0.6959 | 3.1289 | 0.2224 |
| google/gemini-3-flash-preview \| crag | 0.7072 | 3.2131 | 0.2201 |
| google/gemini-3-flash-preview \| lightrag | 0.7515 | 1.7056 | 0.4406 |
| mistralai/mistral-large-2512 \| agentic_rag | 0.6700 | 2.5262 | 0.2652 |
| mistralai/mistral-large-2512 \| crag | 0.7656 | 2.5701 | 0.2979 |
| mistralai/mistral-large-2512 \| lightrag | 0.7641 | 1.7394 | 0.4393 |
| mistralai/mistral-small-2603 \| agentic_rag | 0.6904 | 0.9815 | 0.7034 |
| mistralai/mistral-small-2603 \| crag | 0.6908 | 0.8255 | 0.8368 |
| mistralai/mistral-small-2603 \| lightrag | 0.7435 | 0.5517 | 1.3477 |

## Breakdowns

> Values: **avg score ± 95 % CI (n)**.

### By Domain

#### answer_relevancy

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 0.812 ± 0.091 (n=15) | 0.892 ± 0.059 (n=15) | 0.911 ± 0.048 (n=15) | 0.835 ± 0.077 (n=15) | 0.844 ± 0.055 (n=15) | 0.914 ± 0.048 (n=15) | 0.823 ± 0.065 (n=15) | 0.805 ± 0.059 (n=15) | 0.825 ± 0.071 (n=14) |
| controller_processor_obligations | 0.762 ± 0.053 (n=40) | 0.671 ± 0.084 (n=40) | 0.672 ± 0.074 (n=40) | 0.763 ± 0.067 (n=40) | 0.731 ± 0.067 (n=40) | 0.696 ± 0.072 (n=40) | 0.727 ± 0.064 (n=40) | 0.720 ± 0.059 (n=40) | 0.672 ± 0.081 (n=40) |
| cross_cutting | 0.950 ± 0.635 (n=2) | 1.000 ± 0.000 (n=2) | 0.862 ± 0.230 (n=2) | 1.000 ± 0.000 (n=2) | 0.738 ± 1.441 (n=2) | 0.833 ± 2.118 (n=2) | 0.944 ± 0.706 (n=2) | 0.867 ± 1.247 (n=2) | 0.939 ± 0.770 (n=2) |
| data_subject_rights | 0.862 ± 0.077 (n=14) | 0.823 ± 0.083 (n=14) | 0.879 ± 0.069 (n=14) | 0.821 ± 0.128 (n=14) | 0.858 ± 0.083 (n=14) | 0.833 ± 0.068 (n=14) | 0.835 ± 0.078 (n=14) | 0.826 ± 0.072 (n=14) | 0.936 ± 0.044 (n=14) |
| enforcement_and_remedies | 0.880 ± 0.075 (n=3) | 0.982 ± 0.075 (n=3) | 0.986 ± 0.062 (n=3) | 0.951 ± 0.152 (n=3) | 0.928 ± 0.161 (n=3) | 0.906 ± 0.365 (n=3) | 0.954 ± 0.199 (n=3) | 0.891 ± 0.276 (n=3) | 0.964 ± 0.084 (n=3) |
| principles_and_lawfulness | 0.815 ± 0.035 (n=75) | 0.777 ± 0.044 (n=75) | 0.695 ± 0.048 (n=75) | 0.785 ± 0.049 (n=75) | 0.806 ± 0.035 (n=75) | 0.732 ± 0.053 (n=75) | 0.770 ± 0.045 (n=75) | 0.781 ± 0.036 (n=75) | 0.722 ± 0.053 (n=75) |
| supervisory_authorities | 0.667 ± 0.000 (n=1) | 0.625 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 0.647 ± 0.000 (n=1) | 0.533 ± 0.000 (n=1) | 0.733 ± 0.000 (n=1) | 0.750 ± 0.000 (n=1) | 0.818 ± 0.000 (n=1) | 0.957 ± 0.000 (n=1) |
| transfers | 0.773 ± 0.496 (n=3) | 0.892 ± 0.090 (n=3) | 0.987 ± 0.057 (n=3) | 0.901 ± 0.213 (n=3) | 0.832 ± 0.283 (n=3) | 0.964 ± 0.156 (n=3) | 0.909 ± 0.132 (n=3) | 0.990 ± 0.043 (n=3) | 0.937 ± 0.116 (n=3) |

#### context_precision

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 0.228 ± 0.197 (n=15) | 0.653 ± 0.187 (n=14) | 0.777 ± 0.161 (n=10) | 0.278 ± 0.220 (n=15) | 0.801 ± 0.154 (n=15) | 0.645 ± 0.191 (n=11) | 0.484 ± 0.214 (n=15) | 0.715 ± 0.152 (n=15) | 0.688 ± 0.171 (n=11) |
| controller_processor_obligations | 0.528 ± 0.143 (n=40) | 0.522 ± 0.116 (n=40) | 0.431 ± 0.130 (n=34) | 0.538 ± 0.144 (n=40) | 0.593 ± 0.097 (n=40) | 0.444 ± 0.124 (n=37) | 0.621 ± 0.137 (n=40) | 0.439 ± 0.124 (n=40) | 0.468 ± 0.141 (n=36) |
| cross_cutting | 0.500 ± 6.353 (n=2) | 0.780 ± 0.127 (n=2) | N/A | 0.451 ± 5.735 (n=2) | 0.964 ± 0.456 (n=2) | 0.723 ± 0.762 (n=2) | 0.500 ± 6.353 (n=2) | 0.822 ± 0.214 (n=2) | N/A |
| data_subject_rights | 0.720 ± 0.205 (n=14) | 0.606 ± 0.145 (n=14) | 0.762 ± 0.150 (n=13) | 0.760 ± 0.171 (n=14) | 0.657 ± 0.150 (n=14) | 0.654 ± 0.203 (n=9) | 0.746 ± 0.167 (n=14) | 0.673 ± 0.126 (n=14) | 0.603 ± 0.154 (n=12) |
| enforcement_and_remedies | 0.837 ± 0.702 (n=3) | 0.526 ± 0.789 (n=3) | 0.442 ± 0.460 (n=3) | 0.830 ± 0.730 (n=3) | 0.695 ± 0.949 (n=3) | 0.548 ± 0.000 (n=1) | 0.634 ± 0.624 (n=3) | 0.579 ± 0.775 (n=3) | 0.155 ± 1.966 (n=2) |
| principles_and_lawfulness | 0.478 ± 0.088 (n=75) | 0.527 ± 0.095 (n=74) | 0.559 ± 0.096 (n=69) | 0.375 ± 0.088 (n=75) | 0.630 ± 0.075 (n=75) | 0.534 ± 0.096 (n=71) | 0.427 ± 0.090 (n=75) | 0.507 ± 0.086 (n=75) | 0.459 ± 0.095 (n=69) |
| supervisory_authorities | 0.887 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 0.888 ± 0.000 (n=1) | 0.887 ± 0.000 (n=1) | 0.318 ± 0.000 (n=1) | 0.811 ± 0.000 (n=1) | 0.887 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) |
| transfers | 0.844 ± 0.295 (n=3) | 0.795 ± 0.285 (n=3) | 0.899 ± 0.434 (n=3) | 0.882 ± 0.293 (n=3) | 0.749 ± 0.287 (n=3) | 0.804 ± 0.000 (n=2) | 0.877 ± 0.170 (n=3) | 0.780 ± 0.300 (n=3) | 0.920 ± 0.255 (n=3) |

#### context_recall

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 0.267 ± 0.253 (n=15) | 0.733 ± 0.253 (n=15) | 1.000 ± 0.000 (n=15) | 0.333 ± 0.270 (n=15) | 0.800 ± 0.229 (n=15) | 0.933 ± 0.143 (n=15) | 0.533 ± 0.286 (n=15) | 0.733 ± 0.253 (n=15) | 0.933 ± 0.143 (n=15) |
| controller_processor_obligations | 0.437 ± 0.130 (n=40) | 0.485 ± 0.119 (n=40) | 0.613 ± 0.126 (n=40) | 0.433 ± 0.130 (n=40) | 0.651 ± 0.113 (n=40) | 0.616 ± 0.120 (n=40) | 0.527 ± 0.120 (n=40) | 0.427 ± 0.122 (n=40) | 0.614 ± 0.125 (n=40) |
| cross_cutting | 0.286 ± 3.630 (n=2) | 0.000 ± 0.000 (n=2) | 0.929 ± 0.908 (n=2) | 0.286 ± 3.630 (n=2) | 0.125 ± 1.588 (n=2) | 1.000 ± 0.000 (n=2) | 0.250 ± 3.177 (n=2) | 0.071 ± 0.908 (n=2) | 1.000 ± 0.000 (n=2) |
| data_subject_rights | 0.759 ± 0.204 (n=14) | 0.813 ± 0.130 (n=14) | 0.986 ± 0.031 (n=14) | 0.830 ± 0.171 (n=14) | 0.821 ± 0.129 (n=14) | 0.986 ± 0.031 (n=14) | 0.832 ± 0.166 (n=14) | 0.810 ± 0.132 (n=14) | 0.971 ± 0.062 (n=14) |
| enforcement_and_remedies | 0.389 ± 0.862 (n=3) | 0.222 ± 0.956 (n=3) | 0.593 ± 1.304 (n=3) | 0.333 ± 0.828 (n=3) | 0.259 ± 0.887 (n=3) | 0.481 ± 1.245 (n=3) | 0.444 ± 1.265 (n=3) | 0.000 ± 0.000 (n=3) | 0.556 ± 1.265 (n=3) |
| principles_and_lawfulness | 0.398 ± 0.100 (n=74) | 0.474 ± 0.104 (n=75) | 0.559 ± 0.104 (n=74) | 0.269 ± 0.088 (n=75) | 0.555 ± 0.100 (n=75) | 0.558 ± 0.107 (n=71) | 0.317 ± 0.093 (n=75) | 0.450 ± 0.102 (n=75) | 0.548 ± 0.107 (n=72) |
| supervisory_authorities | 0.143 ± 0.000 (n=1) | 0.143 ± 0.000 (n=1) | 0.714 ± 0.000 (n=1) | 0.143 ± 0.000 (n=1) | 0.143 ± 0.000 (n=1) | 0.889 ± 0.000 (n=1) | 0.143 ± 0.000 (n=1) | 0.143 ± 0.000 (n=1) | 0.714 ± 0.000 (n=1) |
| transfers | 0.767 ± 0.625 (n=3) | 0.933 ± 0.287 (n=3) | 1.000 ± 0.000 (n=3) | 0.889 ± 0.478 (n=3) | 0.933 ± 0.287 (n=3) | 1.000 ± 0.000 (n=3) | 0.933 ± 0.287 (n=3) | 0.767 ± 0.625 (n=3) | 1.000 ± 0.000 (n=3) |

#### context_relevancy

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 0.189 ± 0.169 (n=15) | 0.764 ± 0.073 (n=15) | 0.599 ± 0.090 (n=7) | 0.232 ± 0.170 (n=15) | 0.796 ± 0.078 (n=15) | 0.549 ± 0.099 (n=9) | 0.389 ± 0.172 (n=15) | 0.694 ± 0.106 (n=15) | 0.563 ± 0.085 (n=12) |
| controller_processor_obligations | 0.326 ± 0.112 (n=40) | 0.452 ± 0.110 (n=40) | 0.407 ± 0.106 (n=25) | 0.352 ± 0.112 (n=40) | 0.571 ± 0.089 (n=40) | 0.392 ± 0.085 (n=29) | 0.351 ± 0.102 (n=40) | 0.365 ± 0.110 (n=40) | 0.378 ± 0.095 (n=30) |
| cross_cutting | 0.255 ± 3.244 (n=2) | 0.871 ± 0.481 (n=2) | 0.531 ± 0.000 (n=1) | 0.198 ± 2.521 (n=2) | 0.886 ± 0.289 (n=2) | 0.614 ± 0.547 (n=2) | 0.277 ± 3.517 (n=2) | 0.581 ± 1.409 (n=2) | 0.596 ± 0.668 (n=2) |
| data_subject_rights | 0.500 ± 0.172 (n=14) | 0.687 ± 0.156 (n=14) | 0.578 ± 0.070 (n=5) | 0.538 ± 0.138 (n=14) | 0.760 ± 0.082 (n=14) | 0.511 ± 0.119 (n=13) | 0.534 ± 0.145 (n=14) | 0.607 ± 0.131 (n=14) | 0.471 ± 0.122 (n=13) |
| enforcement_and_remedies | 0.547 ± 0.781 (n=3) | 0.917 ± 0.212 (n=3) | 0.561 ± 0.244 (n=3) | 0.532 ± 0.597 (n=3) | 0.921 ± 0.111 (n=3) | 0.525 ± 0.309 (n=3) | 0.629 ± 0.138 (n=3) | 0.899 ± 0.102 (n=3) | 0.534 ± 0.276 (n=3) |
| principles_and_lawfulness | 0.267 ± 0.058 (n=75) | 0.382 ± 0.066 (n=75) | 0.495 ± 0.058 (n=25) | 0.246 ± 0.059 (n=75) | 0.509 ± 0.053 (n=75) | 0.429 ± 0.061 (n=34) | 0.270 ± 0.061 (n=75) | 0.343 ± 0.064 (n=75) | 0.367 ± 0.053 (n=58) |
| supervisory_authorities | 0.043 ± 0.000 (n=1) | 0.800 ± 0.000 (n=1) | 0.543 ± 0.000 (n=1) | 0.042 ± 0.000 (n=1) | 0.400 ± 0.000 (n=1) | 0.455 ± 0.000 (n=1) | 0.042 ± 0.000 (n=1) | 0.200 ± 0.000 (n=1) | 0.541 ± 0.000 (n=1) |
| transfers | 0.826 ± 0.115 (n=3) | 0.733 ± 0.338 (n=3) | 0.665 ± 1.343 (n=2) | 0.703 ± 0.127 (n=3) | 0.762 ± 0.113 (n=3) | 0.717 ± 0.097 (n=3) | 0.806 ± 0.128 (n=3) | 0.688 ± 0.052 (n=3) | 0.781 ± 0.097 (n=3) |

#### faithfulness

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 0.976 ± 0.065 (n=5) | 0.985 ± 0.018 (n=15) | 0.992 ± 0.017 (n=14) | 1.000 ± 0.000 (n=6) | 0.965 ± 0.034 (n=15) | 0.988 ± 0.014 (n=15) | 0.969 ± 0.040 (n=10) | 0.958 ± 0.028 (n=15) | 0.992 ± 0.013 (n=15) |
| controller_processor_obligations | 0.963 ± 0.037 (n=36) | 0.977 ± 0.019 (n=40) | 0.985 ± 0.016 (n=40) | 0.982 ± 0.013 (n=37) | 0.969 ± 0.021 (n=40) | 0.997 ± 0.004 (n=39) | 0.947 ± 0.034 (n=40) | 0.978 ± 0.013 (n=40) | 0.994 ± 0.007 (n=40) |
| cross_cutting | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=1) | 0.964 ± 0.454 (n=2) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=1) | 0.971 ± 0.374 (n=2) | 1.000 ± 0.000 (n=2) |
| data_subject_rights | 0.968 ± 0.038 (n=12) | 0.981 ± 0.032 (n=14) | 0.991 ± 0.013 (n=14) | 0.971 ± 0.043 (n=13) | 0.997 ± 0.007 (n=14) | 0.996 ± 0.008 (n=14) | 0.939 ± 0.065 (n=13) | 0.987 ± 0.029 (n=14) | 0.989 ± 0.017 (n=14) |
| enforcement_and_remedies | 1.000 ± 0.000 (n=3) | 0.974 ± 0.110 (n=3) | 1.000 ± 0.000 (n=3) | 0.939 ± 0.133 (n=3) | 0.923 ± 0.331 (n=3) | 0.909 ± 0.275 (n=3) | 1.000 ± 0.000 (n=3) | 1.000 ± 0.000 (n=3) | 0.956 ± 0.191 (n=3) |
| principles_and_lawfulness | 0.976 ± 0.013 (n=67) | 0.996 ± 0.006 (n=75) | 0.995 ± 0.005 (n=75) | 0.974 ± 0.022 (n=64) | 0.967 ± 0.015 (n=75) | 0.995 ± 0.006 (n=74) | 0.975 ± 0.012 (n=67) | 0.978 ± 0.013 (n=75) | 0.994 ± 0.005 (n=72) |
| supervisory_authorities | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 0.889 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) |
| transfers | 1.000 ± 0.000 (n=3) | 1.000 ± 0.000 (n=3) | 0.979 ± 0.090 (n=3) | 1.000 ± 0.000 (n=3) | 0.976 ± 0.102 (n=3) | 1.000 ± 0.000 (n=3) | 0.935 ± 0.179 (n=3) | 1.000 ± 0.000 (n=3) | 1.000 ± 0.000 (n=3) |

#### legal_interpretability

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 1.000 ± 0.000 (n=15) | 1.000 ± 0.000 (n=15) | 1.000 ± 0.000 (n=15) | 0.933 ± 0.034 (n=15) | 0.980 ± 0.031 (n=15) | 1.000 ± 0.000 (n=15) | 0.920 ± 0.048 (n=15) | 0.927 ± 0.114 (n=15) | 1.000 ± 0.000 (n=15) |
| controller_processor_obligations | 0.982 ± 0.035 (n=40) | 1.000 ± 0.000 (n=40) | 0.930 ± 0.068 (n=40) | 0.918 ± 0.050 (n=40) | 0.915 ± 0.070 (n=40) | 0.953 ± 0.053 (n=40) | 0.955 ± 0.045 (n=40) | 0.905 ± 0.079 (n=40) | 0.972 ± 0.040 (n=40) |
| cross_cutting | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 0.900 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 0.950 ± 0.635 (n=2) |
| data_subject_rights | 1.000 ± 0.000 (n=14) | 1.000 ± 0.000 (n=14) | 1.000 ± 0.000 (n=14) | 0.964 ± 0.029 (n=14) | 0.957 ± 0.044 (n=14) | 1.000 ± 0.000 (n=14) | 0.971 ± 0.048 (n=14) | 0.993 ± 0.015 (n=14) | 1.000 ± 0.000 (n=14) |
| enforcement_and_remedies | 1.000 ± 0.000 (n=3) | 1.000 ± 0.000 (n=3) | 1.000 ± 0.000 (n=3) | 0.933 ± 0.143 (n=3) | 0.967 ± 0.143 (n=3) | 1.000 ± 0.000 (n=3) | 0.833 ± 0.287 (n=3) | 0.967 ± 0.143 (n=3) | 1.000 ± 0.000 (n=3) |
| principles_and_lawfulness | 1.000 ± 0.000 (n=75) | 0.953 ± 0.035 (n=75) | 0.936 ± 0.041 (n=75) | 0.951 ± 0.031 (n=75) | 0.973 ± 0.028 (n=75) | 0.989 ± 0.021 (n=75) | 0.977 ± 0.026 (n=75) | 0.952 ± 0.046 (n=75) | 0.972 ± 0.028 (n=75) |
| supervisory_authorities | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) |
| transfers | 1.000 ± 0.000 (n=3) | 0.933 ± 0.287 (n=3) | 1.000 ± 0.000 (n=3) | 0.900 ± 0.248 (n=3) | 1.000 ± 0.000 (n=3) | 1.000 ± 0.000 (n=3) | 0.900 ± 0.430 (n=3) | 0.933 ± 0.143 (n=3) | 1.000 ± 0.000 (n=3) |

#### regulatory_grounding

| domain | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ai_act | 0.567 ± 0.231 (n=15) | 0.767 ± 0.143 (n=15) | 0.787 ± 0.151 (n=15) | 0.653 ± 0.266 (n=15) | 0.780 ± 0.150 (n=15) | 0.920 ± 0.099 (n=15) | 0.700 ± 0.225 (n=15) | 0.767 ± 0.143 (n=15) | 0.880 ± 0.122 (n=15) |
| controller_processor_obligations | 0.985 ± 0.030 (n=40) | 0.700 ± 0.077 (n=40) | 0.690 ± 0.104 (n=40) | 0.890 ± 0.074 (n=40) | 0.780 ± 0.077 (n=40) | 0.708 ± 0.133 (n=40) | 0.903 ± 0.073 (n=40) | 0.603 ± 0.110 (n=40) | 0.710 ± 0.120 (n=40) |
| cross_cutting | 0.900 ± 1.271 (n=2) | 0.750 ± 3.177 (n=2) | 0.500 ± 0.000 (n=2) | 1.000 ± 0.000 (n=2) | 0.750 ± 3.177 (n=2) | 0.650 ± 1.906 (n=2) | 0.500 ± 6.353 (n=2) | 0.750 ± 3.177 (n=2) | 1.000 ± 0.000 (n=2) |
| data_subject_rights | 0.843 ± 0.133 (n=14) | 0.464 ± 0.077 (n=14) | 0.850 ± 0.143 (n=14) | 0.836 ± 0.194 (n=14) | 0.729 ± 0.175 (n=14) | 1.000 ± 0.000 (n=14) | 0.871 ± 0.142 (n=14) | 0.650 ± 0.161 (n=14) | 0.914 ± 0.106 (n=14) |
| enforcement_and_remedies | 1.000 ± 0.000 (n=3) | 0.833 ± 0.717 (n=3) | 0.633 ± 0.799 (n=3) | 1.000 ± 0.000 (n=3) | 0.833 ± 0.717 (n=3) | 1.000 ± 0.000 (n=3) | 0.900 ± 0.248 (n=3) | 0.967 ± 0.143 (n=3) | 1.000 ± 0.000 (n=3) |
| principles_and_lawfulness | 0.903 ± 0.056 (n=75) | 0.579 ± 0.047 (n=75) | 0.623 ± 0.087 (n=75) | 0.889 ± 0.057 (n=75) | 0.775 ± 0.066 (n=75) | 0.796 ± 0.084 (n=75) | 0.816 ± 0.073 (n=75) | 0.684 ± 0.067 (n=75) | 0.801 ± 0.080 (n=75) |
| supervisory_authorities | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) | 0.500 ± 0.000 (n=1) | 1.000 ± 0.000 (n=1) |
| transfers | 1.000 ± 0.000 (n=3) | 0.833 ± 0.717 (n=3) | 0.667 ± 0.717 (n=3) | 1.000 ± 0.000 (n=3) | 0.833 ± 0.717 (n=3) | 0.833 ± 0.717 (n=3) | 0.833 ± 0.717 (n=3) | 0.833 ± 0.717 (n=3) | 1.000 ± 0.000 (n=3) |

### By Difficulty Bucket Coarse

#### answer_relevancy

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 0.747 ± 0.040 (n=72) | 0.720 ± 0.056 (n=72) | 0.677 ± 0.057 (n=72) | 0.740 ± 0.053 (n=72) | 0.746 ± 0.039 (n=72) | 0.685 ± 0.058 (n=72) | 0.721 ± 0.049 (n=72) | 0.733 ± 0.039 (n=72) | 0.672 ± 0.060 (n=71) |
| medium (0.25–0.5) | 0.860 ± 0.028 (n=75) | 0.820 ± 0.041 (n=75) | 0.796 ± 0.040 (n=75) | 0.839 ± 0.040 (n=75) | 0.834 ± 0.037 (n=75) | 0.819 ± 0.037 (n=75) | 0.822 ± 0.034 (n=75) | 0.817 ± 0.034 (n=75) | 0.823 ± 0.041 (n=75) |
| hard (0.5–0.75) | 0.859 ± 0.127 (n=6) | 0.824 ± 0.151 (n=6) | 0.860 ± 0.144 (n=6) | 0.909 ± 0.140 (n=6) | 0.891 ± 0.186 (n=6) | 0.893 ± 0.110 (n=6) | 0.917 ± 0.101 (n=6) | 0.853 ± 0.102 (n=6) | 0.786 ± 0.241 (n=6) |

#### context_precision

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 0.416 ± 0.102 (n=72) | 0.520 ± 0.088 (n=71) | 0.453 ± 0.096 (n=65) | 0.334 ± 0.097 (n=72) | 0.635 ± 0.074 (n=72) | 0.439 ± 0.093 (n=65) | 0.416 ± 0.098 (n=72) | 0.493 ± 0.085 (n=72) | 0.413 ± 0.094 (n=63) |
| medium (0.25–0.5) | 0.587 ± 0.087 (n=75) | 0.567 ± 0.085 (n=74) | 0.662 ± 0.087 (n=62) | 0.595 ± 0.088 (n=75) | 0.649 ± 0.069 (n=75) | 0.631 ± 0.088 (n=63) | 0.634 ± 0.086 (n=75) | 0.570 ± 0.083 (n=75) | 0.580 ± 0.093 (n=65) |
| hard (0.5–0.75) | 0.568 ± 0.253 (n=6) | 0.857 ± 0.324 (n=6) | 0.888 ± 0.066 (n=6) | 0.457 ± 0.388 (n=6) | 0.720 ± 0.468 (n=6) | 0.578 ± 0.477 (n=6) | 0.571 ± 0.275 (n=6) | 0.700 ± 0.347 (n=6) | 0.618 ± 0.507 (n=6) |

#### context_recall

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 0.332 ± 0.092 (n=71) | 0.565 ± 0.099 (n=72) | 0.674 ± 0.095 (n=71) | 0.300 ± 0.092 (n=72) | 0.727 ± 0.085 (n=72) | 0.647 ± 0.100 (n=68) | 0.389 ± 0.097 (n=72) | 0.516 ± 0.098 (n=72) | 0.627 ± 0.103 (n=69) |
| medium (0.25–0.5) | 0.561 ± 0.100 (n=75) | 0.535 ± 0.098 (n=75) | 0.713 ± 0.093 (n=75) | 0.490 ± 0.100 (n=75) | 0.568 ± 0.095 (n=75) | 0.727 ± 0.090 (n=75) | 0.549 ± 0.097 (n=75) | 0.512 ± 0.101 (n=75) | 0.733 ± 0.089 (n=75) |
| hard (0.5–0.75) | 0.024 ± 0.061 (n=6) | 0.024 ± 0.061 (n=6) | 0.119 ± 0.306 (n=6) | 0.024 ± 0.061 (n=6) | 0.024 ± 0.061 (n=6) | 0.148 ± 0.381 (n=6) | 0.024 ± 0.061 (n=6) | 0.024 ± 0.061 (n=6) | 0.119 ± 0.306 (n=6) |

#### context_relevancy

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 0.250 ± 0.073 (n=72) | 0.488 ± 0.083 (n=72) | 0.404 ± 0.085 (n=25) | 0.210 ± 0.071 (n=72) | 0.615 ± 0.065 (n=72) | 0.430 ± 0.066 (n=41) | 0.270 ± 0.076 (n=72) | 0.399 ± 0.080 (n=72) | 0.364 ± 0.063 (n=52) |
| medium (0.25–0.5) | 0.372 ± 0.069 (n=75) | 0.503 ± 0.069 (n=75) | 0.535 ± 0.054 (n=42) | 0.409 ± 0.064 (n=75) | 0.591 ± 0.053 (n=75) | 0.476 ± 0.054 (n=50) | 0.417 ± 0.060 (n=75) | 0.460 ± 0.067 (n=75) | 0.454 ± 0.054 (n=64) |
| hard (0.5–0.75) | 0.289 ± 0.149 (n=6) | 0.414 ± 0.209 (n=6) | 0.574 ± 0.393 (n=2) | 0.306 ± 0.162 (n=6) | 0.374 ± 0.094 (n=6) | 0.504 ± 0.108 (n=3) | 0.302 ± 0.186 (n=6) | 0.356 ± 0.172 (n=6) | 0.525 ± 0.079 (n=6) |

#### faithfulness

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 0.962 ± 0.026 (n=57) | 0.990 ± 0.009 (n=72) | 0.992 ± 0.006 (n=71) | 0.983 ± 0.015 (n=53) | 0.969 ± 0.014 (n=72) | 0.992 ± 0.007 (n=71) | 0.960 ± 0.022 (n=61) | 0.976 ± 0.014 (n=72) | 0.993 ± 0.006 (n=70) |
| medium (0.25–0.5) | 0.982 ± 0.009 (n=65) | 0.985 ± 0.011 (n=75) | 0.992 ± 0.009 (n=75) | 0.973 ± 0.020 (n=69) | 0.974 ± 0.014 (n=75) | 0.994 ± 0.007 (n=74) | 0.967 ± 0.017 (n=71) | 0.978 ± 0.010 (n=75) | 0.992 ± 0.006 (n=74) |
| hard (0.5–0.75) | 0.974 ± 0.066 (n=6) | 1.000 ± 0.000 (n=6) | 0.988 ± 0.031 (n=6) | 0.971 ± 0.050 (n=6) | 0.924 ± 0.098 (n=6) | 1.000 ± 0.000 (n=6) | 0.956 ± 0.051 (n=6) | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) |

#### legal_interpretability

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 1.000 ± 0.000 (n=72) | 0.960 ± 0.034 (n=72) | 0.921 ± 0.049 (n=72) | 0.931 ± 0.036 (n=72) | 0.946 ± 0.046 (n=72) | 0.964 ± 0.036 (n=72) | 0.956 ± 0.031 (n=72) | 0.908 ± 0.059 (n=72) | 0.971 ± 0.030 (n=72) |
| medium (0.25–0.5) | 0.991 ± 0.019 (n=75) | 0.995 ± 0.011 (n=75) | 0.984 ± 0.021 (n=75) | 0.945 ± 0.024 (n=75) | 0.967 ± 0.017 (n=75) | 0.999 ± 0.003 (n=75) | 0.973 ± 0.016 (n=75) | 0.981 ± 0.022 (n=75) | 0.984 ± 0.021 (n=75) |
| hard (0.5–0.75) | 1.000 ± 0.000 (n=6) | 0.933 ± 0.171 (n=6) | 0.883 ± 0.300 (n=6) | 0.983 ± 0.043 (n=6) | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) | 0.883 ± 0.300 (n=6) | 0.850 ± 0.386 (n=6) | 1.000 ± 0.000 (n=6) |

#### regulatory_grounding

| difficulty_bucket_coarse | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| easy (≤0.25) | 0.815 ± 0.071 (n=72) | 0.679 ± 0.059 (n=72) | 0.647 ± 0.084 (n=72) | 0.781 ± 0.084 (n=72) | 0.724 ± 0.066 (n=72) | 0.707 ± 0.096 (n=72) | 0.767 ± 0.082 (n=72) | 0.632 ± 0.072 (n=72) | 0.726 ± 0.089 (n=72) |
| medium (0.25–0.5) | 0.953 ± 0.043 (n=75) | 0.584 ± 0.048 (n=75) | 0.691 ± 0.077 (n=75) | 0.952 ± 0.036 (n=75) | 0.808 ± 0.059 (n=75) | 0.889 ± 0.062 (n=75) | 0.880 ± 0.059 (n=75) | 0.716 ± 0.067 (n=75) | 0.869 ± 0.062 (n=75) |
| hard (0.5–0.75) | 1.000 ± 0.000 (n=6) | 0.700 ± 0.257 (n=6) | 0.917 ± 0.214 (n=6) | 0.867 ± 0.254 (n=6) | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) | 0.700 ± 0.364 (n=6) | 1.000 ± 0.000 (n=6) |

### By Answer Type

#### answer_relevancy

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 0.904 ± 0.034 (n=22) | 0.865 ± 0.053 (n=22) | 0.787 ± 0.065 (n=22) | 0.910 ± 0.041 (n=22) | 0.882 ± 0.050 (n=22) | 0.875 ± 0.038 (n=22) | 0.917 ± 0.031 (n=22) | 0.857 ± 0.053 (n=22) | 0.834 ± 0.068 (n=22) |
| comparative | 0.884 ± 0.115 (n=6) | 0.889 ± 0.130 (n=6) | 0.890 ± 0.101 (n=6) | 0.935 ± 0.084 (n=6) | 0.766 ± 0.172 (n=6) | 0.772 ± 0.168 (n=6) | 0.799 ± 0.153 (n=6) | 0.780 ± 0.174 (n=6) | 0.859 ± 0.205 (n=6) |
| definitional | 0.812 ± 0.083 (n=19) | 0.819 ± 0.123 (n=19) | 0.784 ± 0.081 (n=19) | 0.764 ± 0.090 (n=19) | 0.805 ± 0.066 (n=19) | 0.728 ± 0.103 (n=19) | 0.758 ± 0.089 (n=19) | 0.764 ± 0.080 (n=19) | 0.774 ± 0.105 (n=19) |
| enumerative | 0.741 ± 0.043 (n=52) | 0.685 ± 0.063 (n=52) | 0.631 ± 0.074 (n=52) | 0.711 ± 0.067 (n=52) | 0.714 ± 0.050 (n=52) | 0.654 ± 0.070 (n=52) | 0.687 ± 0.058 (n=52) | 0.714 ± 0.050 (n=52) | 0.621 ± 0.071 (n=51) |
| procedural | 0.818 ± 0.044 (n=53) | 0.790 ± 0.052 (n=53) | 0.805 ± 0.044 (n=53) | 0.824 ± 0.050 (n=53) | 0.835 ± 0.044 (n=53) | 0.822 ± 0.050 (n=53) | 0.818 ± 0.044 (n=53) | 0.817 ± 0.037 (n=53) | 0.819 ± 0.051 (n=53) |

#### context_precision

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 0.494 ± 0.128 (n=22) | 0.514 ± 0.178 (n=22) | 0.778 ± 0.120 (n=21) | 0.482 ± 0.124 (n=22) | 0.696 ± 0.150 (n=22) | 0.783 ± 0.130 (n=22) | 0.515 ± 0.125 (n=22) | 0.553 ± 0.154 (n=22) | 0.677 ± 0.169 (n=20) |
| comparative | 0.534 ± 0.488 (n=6) | 0.675 ± 0.460 (n=5) | 0.793 ± 0.242 (n=5) | 0.528 ± 0.478 (n=6) | 0.737 ± 0.307 (n=6) | 0.714 ± 0.250 (n=6) | 0.831 ± 0.231 (n=6) | 0.690 ± 0.317 (n=6) | 0.954 ± 0.146 (n=4) |
| definitional | 0.531 ± 0.214 (n=19) | 0.794 ± 0.104 (n=19) | 0.781 ± 0.159 (n=14) | 0.346 ± 0.213 (n=19) | 0.802 ± 0.090 (n=19) | 0.700 ± 0.125 (n=16) | 0.475 ± 0.214 (n=19) | 0.663 ± 0.103 (n=19) | 0.574 ± 0.169 (n=17) |
| enumerative | 0.373 ± 0.121 (n=52) | 0.468 ± 0.109 (n=51) | 0.340 ± 0.115 (n=46) | 0.362 ± 0.119 (n=52) | 0.578 ± 0.096 (n=52) | 0.342 ± 0.111 (n=46) | 0.379 ± 0.118 (n=52) | 0.435 ± 0.108 (n=52) | 0.308 ± 0.106 (n=47) |
| procedural | 0.621 ± 0.105 (n=53) | 0.554 ± 0.097 (n=53) | 0.610 ± 0.101 (n=46) | 0.590 ± 0.113 (n=53) | 0.619 ± 0.079 (n=53) | 0.529 ± 0.112 (n=44) | 0.659 ± 0.102 (n=53) | 0.566 ± 0.102 (n=53) | 0.567 ± 0.111 (n=45) |

#### context_recall

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 0.348 ± 0.211 (n=22) | 0.508 ± 0.217 (n=22) | 0.481 ± 0.222 (n=22) | 0.367 ± 0.209 (n=22) | 0.502 ± 0.214 (n=22) | 0.473 ± 0.218 (n=22) | 0.285 ± 0.194 (n=22) | 0.394 ± 0.217 (n=22) | 0.478 ± 0.219 (n=22) |
| comparative | 0.395 ± 0.476 (n=6) | 0.670 ± 0.468 (n=6) | 0.810 ± 0.201 (n=6) | 0.429 ± 0.519 (n=6) | 0.727 ± 0.372 (n=6) | 0.823 ± 0.289 (n=6) | 0.685 ± 0.304 (n=6) | 0.537 ± 0.471 (n=6) | 0.867 ± 0.227 (n=6) |
| definitional | 0.472 ± 0.235 (n=18) | 0.636 ± 0.192 (n=19) | 0.889 ± 0.109 (n=19) | 0.307 ± 0.213 (n=19) | 0.672 ± 0.186 (n=19) | 0.882 ± 0.111 (n=19) | 0.424 ± 0.226 (n=19) | 0.705 ± 0.175 (n=19) | 0.889 ± 0.115 (n=19) |
| enumerative | 0.378 ± 0.106 (n=52) | 0.471 ± 0.114 (n=52) | 0.595 ± 0.118 (n=51) | 0.348 ± 0.104 (n=52) | 0.711 ± 0.098 (n=52) | 0.580 ± 0.118 (n=49) | 0.413 ± 0.109 (n=52) | 0.415 ± 0.113 (n=52) | 0.555 ± 0.125 (n=49) |
| procedural | 0.502 ± 0.120 (n=53) | 0.532 ± 0.119 (n=53) | 0.724 ± 0.110 (n=53) | 0.432 ± 0.120 (n=53) | 0.547 ± 0.117 (n=53) | 0.729 ± 0.111 (n=52) | 0.535 ± 0.118 (n=53) | 0.526 ± 0.117 (n=53) | 0.720 ± 0.108 (n=53) |

#### context_relevancy

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 0.359 ± 0.067 (n=22) | 0.377 ± 0.065 (n=22) | 0.545 ± 0.112 (n=11) | 0.388 ± 0.059 (n=22) | 0.477 ± 0.079 (n=22) | 0.530 ± 0.055 (n=12) | 0.369 ± 0.061 (n=22) | 0.446 ± 0.087 (n=22) | 0.466 ± 0.071 (n=22) |
| comparative | 0.297 ± 0.244 (n=6) | 0.650 ± 0.291 (n=6) | 0.478 ± 0.593 (n=3) | 0.332 ± 0.307 (n=6) | 0.684 ± 0.313 (n=6) | 0.522 ± 0.157 (n=5) | 0.383 ± 0.251 (n=6) | 0.493 ± 0.285 (n=6) | 0.436 ± 0.270 (n=6) |
| definitional | 0.220 ± 0.121 (n=19) | 0.627 ± 0.123 (n=19) | 0.359 ± 0.171 (n=9) | 0.183 ± 0.134 (n=19) | 0.689 ± 0.111 (n=19) | 0.354 ± 0.126 (n=12) | 0.256 ± 0.141 (n=19) | 0.451 ± 0.127 (n=19) | 0.334 ± 0.108 (n=18) |
| enumerative | 0.273 ± 0.095 (n=52) | 0.437 ± 0.107 (n=52) | 0.441 ± 0.104 (n=19) | 0.252 ± 0.092 (n=52) | 0.564 ± 0.079 (n=52) | 0.418 ± 0.089 (n=26) | 0.287 ± 0.094 (n=52) | 0.355 ± 0.099 (n=52) | 0.366 ± 0.080 (n=35) |
| procedural | 0.359 ± 0.092 (n=53) | 0.523 ± 0.087 (n=53) | 0.543 ± 0.063 (n=26) | 0.377 ± 0.087 (n=53) | 0.625 ± 0.065 (n=53) | 0.483 ± 0.065 (n=39) | 0.408 ± 0.083 (n=53) | 0.466 ± 0.087 (n=53) | 0.475 ± 0.072 (n=40) |

#### faithfulness

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 0.989 ± 0.017 (n=20) | 0.992 ± 0.016 (n=22) | 0.980 ± 0.028 (n=22) | 0.970 ± 0.057 (n=21) | 0.961 ± 0.039 (n=22) | 1.000 ± 0.000 (n=21) | 0.981 ± 0.016 (n=21) | 0.986 ± 0.020 (n=22) | 0.996 ± 0.009 (n=22) |
| comparative | 1.000 ± 0.000 (n=4) | 1.000 ± 0.000 (n=6) | 0.986 ± 0.036 (n=6) | 0.984 ± 0.050 (n=4) | 0.988 ± 0.031 (n=6) | 0.990 ± 0.028 (n=5) | 1.000 ± 0.000 (n=6) | 0.978 ± 0.036 (n=6) | 1.000 ± 0.000 (n=6) |
| definitional | 1.000 ± 0.000 (n=12) | 0.992 ± 0.011 (n=19) | 1.000 ± 0.000 (n=19) | 1.000 ± 0.000 (n=8) | 0.981 ± 0.026 (n=19) | 0.980 ± 0.025 (n=19) | 0.967 ± 0.039 (n=11) | 0.978 ± 0.027 (n=19) | 0.984 ± 0.017 (n=19) |
| enumerative | 0.959 ± 0.030 (n=47) | 0.991 ± 0.009 (n=52) | 0.990 ± 0.009 (n=52) | 0.973 ± 0.019 (n=48) | 0.966 ± 0.018 (n=52) | 0.990 ± 0.010 (n=52) | 0.949 ± 0.027 (n=50) | 0.980 ± 0.012 (n=52) | 0.992 ± 0.008 (n=52) |
| procedural | 0.969 ± 0.016 (n=44) | 0.981 ± 0.015 (n=53) | 0.996 ± 0.004 (n=52) | 0.980 ± 0.015 (n=46) | 0.970 ± 0.015 (n=53) | 0.998 ± 0.002 (n=53) | 0.965 ± 0.021 (n=49) | 0.971 ± 0.016 (n=53) | 0.995 ± 0.005 (n=50) |

#### legal_interpretability

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 1.000 ± 0.000 (n=22) | 0.982 ± 0.038 (n=22) | 0.918 ± 0.096 (n=22) | 0.968 ± 0.032 (n=22) | 0.982 ± 0.022 (n=22) | 1.000 ± 0.000 (n=22) | 0.968 ± 0.066 (n=22) | 0.923 ± 0.111 (n=22) | 0.968 ± 0.066 (n=22) |
| comparative | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) | 0.950 ± 0.088 (n=6) | 0.983 ± 0.043 (n=6) | 0.933 ± 0.171 (n=6) | 0.967 ± 0.086 (n=6) | 1.000 ± 0.000 (n=6) | 1.000 ± 0.000 (n=6) |
| definitional | 1.000 ± 0.000 (n=19) | 0.974 ± 0.055 (n=19) | 1.000 ± 0.000 (n=19) | 0.979 ± 0.020 (n=19) | 0.995 ± 0.011 (n=19) | 0.958 ± 0.088 (n=19) | 0.995 ± 0.011 (n=19) | 1.000 ± 0.000 (n=19) | 0.995 ± 0.011 (n=19) |
| enumerative | 1.000 ± 0.000 (n=52) | 0.958 ± 0.043 (n=52) | 0.894 ± 0.066 (n=52) | 0.890 ± 0.053 (n=52) | 0.923 ± 0.064 (n=52) | 0.973 ± 0.038 (n=52) | 0.940 ± 0.042 (n=52) | 0.871 ± 0.080 (n=52) | 0.962 ± 0.041 (n=52) |
| procedural | 0.987 ± 0.027 (n=53) | 0.989 ± 0.017 (n=53) | 0.994 ± 0.011 (n=53) | 0.960 ± 0.019 (n=53) | 0.966 ± 0.023 (n=53) | 0.998 ± 0.004 (n=53) | 0.966 ± 0.023 (n=53) | 0.991 ± 0.008 (n=53) | 0.991 ± 0.016 (n=53) |

#### regulatory_grounding

| answer_type | google/gemini-3-flash-preview | agentic_rag | google/gemini-3-flash-preview | crag | google/gemini-3-flash-preview | lightrag | mistralai/mistral-large-2512 | agentic_rag | mistralai/mistral-large-2512 | crag | mistralai/mistral-large-2512 | lightrag | mistralai/mistral-small-2603 | agentic_rag | mistralai/mistral-small-2603 | crag | mistralai/mistral-small-2603 | lightrag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| application | 1.000 ± 0.000 (n=22) | 0.600 ± 0.088 (n=22) | 0.741 ± 0.140 (n=22) | 0.964 ± 0.059 (n=22) | 0.955 ± 0.065 (n=22) | 0.955 ± 0.095 (n=22) | 0.859 ± 0.128 (n=22) | 0.873 ± 0.110 (n=22) | 1.000 ± 0.000 (n=22) |
| comparative | 1.000 ± 0.000 (n=6) | 0.667 ± 0.271 (n=6) | 0.750 ± 0.287 (n=6) | 0.967 ± 0.086 (n=6) | 0.700 ± 0.257 (n=6) | 0.817 ± 0.378 (n=6) | 0.800 ± 0.332 (n=6) | 0.583 ± 0.214 (n=6) | 1.000 ± 0.000 (n=6) |
| definitional | 0.795 ± 0.140 (n=19) | 0.605 ± 0.101 (n=19) | 0.789 ± 0.122 (n=19) | 0.800 ± 0.182 (n=19) | 0.711 ± 0.122 (n=19) | 0.795 ± 0.161 (n=19) | 0.700 ± 0.198 (n=19) | 0.653 ± 0.132 (n=19) | 0.905 ± 0.112 (n=19) |
| enumerative | 0.877 ± 0.077 (n=52) | 0.715 ± 0.068 (n=52) | 0.596 ± 0.111 (n=52) | 0.802 ± 0.086 (n=52) | 0.712 ± 0.086 (n=52) | 0.633 ± 0.121 (n=52) | 0.833 ± 0.080 (n=52) | 0.608 ± 0.098 (n=52) | 0.612 ± 0.113 (n=52) |
| procedural | 0.877 ± 0.076 (n=53) | 0.575 ± 0.065 (n=53) | 0.691 ± 0.090 (n=53) | 0.904 ± 0.073 (n=53) | 0.802 ± 0.068 (n=53) | 0.919 ± 0.064 (n=53) | 0.866 ± 0.078 (n=53) | 0.683 ± 0.071 (n=53) | 0.858 ± 0.075 (n=53) |
