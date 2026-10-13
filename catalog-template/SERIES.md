# Series plan

Every playlist is a series taught in order. Vote for what you want first in the [roadmap](ROADMAP.md).

## Neuroscience from Zero

*Science and technology* · शून्य से न्यूरोसाइंस · শূন্য থেকে নিউরোসায়েন্স

How the brain works, from one neuron to whole-brain networks, taught for students with no biology background. Each video builds on the one before it.

| # | Video | Level | You will learn to | Watch first |
|---|-------|-------|-------------------|-------------|
| 1 | What a neuron actually does | Beginner | Explain how a neuron receives, adds up and sends signals. | - |
| 2 | The action potential, step by step | Beginner | Draw the action potential and say which ion does what at each phase. | What a neuron actually does |
| 3 | Synapses: how neurons talk | Beginner | Describe chemical synaptic transmission and excitation versus inhibition. | The action potential, step by step |
| 4 | Dopamine is not the pleasure chemical | Beginner | Explain dopamine as a learning signal (reward prediction error). | Synapses: how neurons talk |
| 5 | How the brain learns: plasticity | Intermediate | Explain Hebbian learning, LTP and why practice changes the brain. | Synapses: how neurons talk |
| 6 | Measuring the brain: EEG, MEG and fMRI | Intermediate | Say what each method measures, and its time and space resolution. | The action potential, step by step |
| 7 | Brain networks and rhythms | Intermediate | Explain oscillations (alpha, gamma...) and functional networks without myths. | Measuring the brain: EEG, MEG and fMRI |
| 8 | Real neurons vs artificial neural networks | Intermediate | Compare what deep learning borrowed from the brain and what it did not. | How the brain learns: plasticity |

Shorts: A neuron is not a wire · All-or-nothing: why neurons spike, not dim · The dopamine myth in 45 seconds

## Signals and Systems, Explained

*Engineering* · सिग्नल और सिस्टम, आसान भाषा में · সিগন্যাল ও সিস্টেম, সহজ ভাষায়

The engineering behind sound, images, sensors and brain recordings: sampling, frequency, filtering and feedback, with Python on real signals.

| # | Video | Level | You will learn to | Watch first |
|---|-------|-------|-------------------|-------------|
| 1 | What is a signal? From sound to EEG | Beginner | Describe signals in time, and the idea of amplitude, frequency and phase. | - |
| 2 | Sampling and the Nyquist rule | Beginner | Choose a sampling rate and explain aliasing with an example. | What is a signal? From sound to EEG |
| 3 | The Fourier transform without fear | Intermediate | Compute and read a spectrum in Python and say what the FFT is doing. | Sampling and the Nyquist rule |
| 4 | Filters: keeping what you want | Intermediate | Design and apply low-, high- and band-pass filters, and see their side effects. | The Fourier transform without fear |
| 5 | Noise, artifacts and cleaning real recordings | Intermediate | Spot and remove line noise and artifacts in a real EEG recording. | Filters: keeping what you want |
| 6 | Feedback and control: how a thermostat thinks | Intermediate | Explain feedback loops and PID control with a simulation. | What is a signal? From sound to EEG |
| 7 | Project: build an EEG band-power analyser in Python | Advanced | Go from a raw open dataset to band-power plots, with code in the repo. | Noise, artifacts and cleaning real recordings |

Shorts: Why wheels spin backwards on video

## Data Analysis from Zero (Python)

*Data analysis* · शून्य से डेटा एनालिसिस (Python) · শূন্য থেকে ডেটা অ্যানালাইসিস (Python)

Real data analysis the correct way: Python, pandas, statistics, plots and machine learning, and how not to fool yourself with numbers.

| # | Video | Level | You will learn to | Watch first |
|---|-------|-------|-------------------|-------------|
| 1 | Set up Python for data analysis | Beginner | Install Python, Jupyter and pandas, and run a first notebook. | - |
| 2 | pandas: load, explore, clean | Beginner | Load a real CSV, find missing and wrong values, and fix them reproducibly. | Set up Python for data analysis |
| 3 | Plots that tell the truth | Beginner | Pick the right chart and avoid misleading axes and averages. | pandas: load, explore, clean |
| 4 | Statistics you actually need | Intermediate | Use mean, median, variance and distributions correctly, with real data. | Plots that tell the truth |
| 5 | p-values, done correctly | Intermediate | Say what a p-value is and is not, and run a test without p-hacking. | Statistics you actually need |
| 6 | Correlation, regression and confounders | Intermediate | Fit a regression and explain why correlation is not causation, with an example. | p-values, done correctly |
| 7 | Machine learning with scikit-learn, honestly | Intermediate | Train, validate and test a model and catch data leakage. | Correlation, regression and confounders |
| 8 | Project: analyse an open dataset end to end | Advanced | Question, clean, analyse, model and present, with the notebook in the repo. | Machine learning with scikit-learn, honestly |

Shorts: The same data, two opposite charts · What a p-value is NOT

## Algo Trading with Python - Education Only

*Algorithmic trading* · Python से एल्गो ट्रेडिंग - केवल शिक्षा के लिए · Python দিয়ে অ্যালগো ট্রেডিং - শুধুমাত্র শিক্ষার জন্য

Markets as a data-science and engineering problem: data, returns, risk, and building and testing a backtester honestly. Education only - not financial advice, no buy or sell calls.

| # | Video | Level | You will learn to | Watch first |
|---|-------|-------|-------------------|-------------|
| 1 | Market data in Python: prices, candles, returns | Beginner | Load price data and compute simple and log returns correctly. | pandas: load, explore, clean |
| 2 | Risk first: volatility and drawdown | Beginner | Measure volatility and maximum drawdown and explain why they matter more than returns. | Market data in Python: prices, candles, returns |
| 3 | Build a backtester from scratch | Intermediate | Write a simple event-by-event backtester and test it on a toy strategy. | Risk first: volatility and drawdown |
| 4 | Costs and slippage: why most backtests lie | Intermediate | Add fees and slippage and show how much they change the result. | Build a backtester from scratch |
| 5 | Overfitting, look-ahead and survivorship bias | Intermediate | Recognise the three biases in real backtests and test against them. | Costs and slippage: why most backtests lie |
| 6 | Walk-forward testing and out-of-sample data | Advanced | Split data properly and validate a strategy walk-forward. | Overfitting, look-ahead and survivorship bias |
| 7 | Position sizing and risk management | Advanced | Size positions by risk and explain why sizing matters more than signals. | Walk-forward testing and out-of-sample data |
| 8 | Paper trading, regulation and staying honest | Advanced | Paper trade safely and know what SEBI rules mean for advice and tips. | Position sizing and risk management |

Shorts: A 50% loss needs a 100% gain · The backtest that was too good to be true

## The Computational Brain: Psychosis Research Explained

*Interdisciplinary research* · कम्प्यूटेशनल ब्रेन: साइकोसिस रिसर्च आसान भाषा में · কম্পিউটেশনাল ব্রেন: সাইকোসিস গবেষণা সহজ ভাষায়

Computational neuroscience applied to psychosis, from a PhD researcher in the field: what psychosis is, the theories that model it, and how the research is actually done. Education only - not medical advice. If you or someone you know is struggling, contact a local helpline or a doctor.

| # | Video | Level | You will learn to | Watch first |
|---|-------|-------|-------------------|-------------|
| 1 | What psychosis is, and what it is not | Beginner | Describe psychosis accurately, without stigma, and separate it from movie myths. | - |
| 2 | What is computational psychiatry? | Beginner | Explain why maths and models are used to study mental illness. | What psychosis is, and what it is not |
| 3 | The predictive brain | Intermediate | Explain predictive coding: the brain as a prediction machine that learns from errors. | Dopamine is not the pleasure chemical |
| 4 | When predictions go wrong: predictive coding and psychosis | Intermediate | Explain how altered prediction and precision could lead to hallucinations and delusions. | The predictive brain |
| 5 | Dopamine and aberrant salience | Intermediate | Explain the aberrant salience hypothesis and what evidence supports and limits it. | When predictions go wrong: predictive coding and psychosis |
| 6 | Modelling belief updating: reinforcement learning and Bayesian models | Advanced | Fit a simple learning model to choice data and read its parameters. | Dopamine and aberrant salience |
| 7 | Brain signals in psychosis: EEG and mismatch negativity | Advanced | Explain mismatch negativity and why it is studied as a marker in psychosis. | Noise, artifacts and cleaning real recordings |
| 8 | Inside my PhD: a computational psychosis study, start to finish | Advanced | Walk through a real study's question, data, model and limits. | Modelling belief updating: reinforcement learning and Bayesian models |

Shorts: Your brain sees what it expects

## Learn It Right: Research Skills for Students

*Learning and research skills* · सही तरीके से सीखें: छात्रों के लिए रिसर्च स्किल्स · সঠিকভাবে শিখুন: ছাত্রছাত্রীদের জন্য রিসার্চ স্কিল

How to learn a new field properly, read papers, start research as a student and keep going. Honest about PhD life, the hard parts included.

| # | Video | Level | You will learn to | Watch first |
|---|-------|-------|-------------------|-------------|
| 1 | How to learn any technical subject properly | Beginner | Use active recall, spaced practice and projects instead of rewatching videos. | - |
| 2 | How to read a research paper | Beginner | Read a paper in three passes and pull out the question, method and limits. | - |
| 3 | Finding papers: Google Scholar, PubMed and arXiv | Beginner | Search the literature systematically and keep track of what you read. | How to read a research paper |
| 4 | Reproduce a paper: the best first research project | Intermediate | Pick a paper with open code and data and reproduce one result. | Finding papers: Google Scholar, PubMed and arXiv |
| 5 | How to start research as an undergraduate | Beginner | Find a lab or project, write to a professor and apply for summer research programmes. | - |
| 6 | Writing your first paper | Intermediate | Structure a paper and know what reviewers look for. | Reproduce a paper: the best first research project |
| 7 | Failure, rejection and motivation in research | Beginner | Handle failed experiments and rejections with a plan, not panic. | - |
| 8 | PhD life, honestly | Beginner | Give a realistic picture of a PhD: time, money, supervision, and what makes it worth it. | - |

Shorts: Rewatching is not learning
