# CS577 — Robot Learning and Interaction

**로봇 학습과 상호 작용 · Fall 2026**

[Original syllabus PDF](cs577-syllabus-fall2026.pdf)

## Course information

| Item | Details |
| --- | --- |
| Instructor | Asst. Prof. Daehyung Park ([daehyung@kaist.ac.kr](mailto:daehyung@kaist.ac.kr)) |
| Office hours | Anytime by appointment |
| Class meetings | Tuesdays and Thursdays, 10:30–12:00 |
| Classroom | E3-1 2443 |
| Teaching assistants | Jaehyung Jang (wogud9019@kaist.ac.kr), Injin Choi (changing@kaist.ac.kr), and Chankyu Lee (chankyu04@kaist.ac.kr) |

## Description and prerequisites

The course introduces graduate students to intelligent robotics for human-centered applications. Topics include learning from demonstration (LfD), reinforcement learning (RL), world models, natural language interaction, and interactive perception. Students review recent research, particularly award-winning and finalist papers, practice techniques with simulated manipulators, and apply them in a final individual or team project.

The syllabus recommends taking CS376, CS470, or CS477 before or alongside CS577. The course requires computing resources. Students who lack both a research lab affiliation and access to adequate computing resources are strongly advised against enrolling.

## Schedule

| Date | Topic or milestone |
| --- | --- |
| Sep 1 (Tue) | Survey for robot learning |
| Sep 3 (Thu) | Learning from demonstrations I |
| Sep 8 (Tue) | Learning from demonstrations II — Dynamic Movement Primitives |
| Sep 10 (Thu) | Reserved for a guest lecture by Dr. Mingyo Seo from the University of Texas at Austin (Assistant Professor at UCF, as listed in the syllabus) |
| Sep 15 (Tue) | Learning from demonstrations III — Diffusion Policy and flow matching |
| Sep 17 (Thu) | Learning from demonstrations IV — Vision-Language-Action (VLA) models |
| Sep 22 (Tue) | Learning from demonstrations IV — VLA models. Team-building and paper assignment sheets open. |
| Sep 24 (Thu) | No class (holiday) |
| Sep 29 (Tue) | No class (IROS) |
| Sep 30 (Wed) | **Assignment 1 due.** |
| Oct 1 (Thu) | Learning from demonstrations IV — VLA models via recorded KLMS lecture, available Oct 5. **Team-building deadline.** |
| Oct 4 (Sun) | **Proposed project title due.** The PDF gives this deadline in the Oct 8 row. |
| Oct 6 (Tue) | Robot world models |
| Oct 8 (Thu) | Reserved for a guest lecture by Dr. Rajat Talak from NUS |
| Oct 13 (Tue) | Reinforcement Learning I — MDP. Reinforcement Learning II — Dynamic Programming. |
| Oct 15 (Thu) | Recorded lecture on KLMS. Reinforcement Learning III — Temporal Difference Learning. Reinforcement Learning IV — Function Approximation. Inverse Reinforcement Learning I. |
| Oct 20 (Tue) | No class (midterm) |
| Oct 22 (Thu) | No class (midterm) |
| Oct 27 (Tue) | **Midterm project proposal.** 5–10 minutes plus Q&A. Cover the problem, potential solution, and experiment plan if applicable. |
| Oct 29 (Thu) | **Midterm project proposal**, continued |
| Oct 31 (Sat) | **Assignment 2 due.** |
| Nov 3 (Tue) | Student presentations — Perception |
| Nov 5 (Thu) | Student presentations — Vision-language-action models |
| Nov 10 (Tue) | Student presentations — Vision-language-action models |
| Nov 12 (Thu) | Student presentations — World models |
| Nov 17 (Tue) | Student presentations — Humanoid robots |
| Nov 19 (Thu) | Student presentations — Humanoid robots |
| Nov 24 (Tue) | Student presentations — World models and other topics |
| Nov 26 (Thu) | No class (undergraduate interviews) |
| Dec 1 (Tue) | Student presentations — Motion and task planning |
| Dec 3 (Thu) | Student presentations — Human-robot interaction |
| Dec 8 (Tue) | **Final paper and presentation session** |
| Dec 10 (Thu) | **Final paper and presentation session** |
| Dec 15 (Tue) | No class (final exam) |
| Dec 17 (Thu) | No class (final exam). **Abstract paper due, two pages in two-column format.** |

### September readings

**Sep 1 — Survey for robot learning**

- Oliver Kroemer, Scott Niekum, and George Konidaris (2019). arXiv:1907.03146. [A Review of Robot Learning for Manipulation: Challenges, Representations, and Algorithms](https://arxiv.org/abs/1907.03146).
- Nicholas Roy, Ingmar Posner, Tim Barfoot, Philippe Beaudoin, Yoshua Bengio, Jeannette Bohg, Oliver Brock, et al. (2021). arXiv:2110.15245. [From Machine Learning to Robotics: Challenges and Opportunities for Embodied Intelligence](https://arxiv.org/abs/2110.15245).

**Sep 3 — Learning from demonstrations I**

- Brenna D. Argall, Sonia Chernova, Manuela Veloso, and Brett Browning (2008). Robotics and Autonomous Systems. [A Survey of Robot Learning from Demonstration](https://www.sciencedirect.com/science/article/pii/S0921889008001772).
- Sylvain Calinon (2018). Encyclopedia of Robotics. [Learning from Demonstration (Programming by Demonstration)](https://www.idiap.ch/~scalinon/papers/Calinon-EncyclopediaRobotics2019.pdf).

**Sep 8 — Dynamic Movement Primitives**

- Peter Pastor, Heiko Hoffmann, Tamim Asfour, and Stefan Schaal (2009). ICRA, pp. 763–768. [Learning and Generalization of Motor Skills by Learning from Demonstration](https://ieeexplore.ieee.org/abstract/document/5152385).
- Heiko Hoffmann, Peter Pastor, Dae-Hyung Park, and Stefan Schaal (2009). ICRA, pp. 2587–2592. [Biologically-Inspired Dynamical Systems for Movement Generation: Automatic Real-Time Goal Adaptation and Obstacle Avoidance](https://ieeexplore.ieee.org/abstract/document/5152423).

**Sep 15 — Diffusion Policy**

- Cheng Chi et al. (2023). The International Journal of Robotics Research, article 02783649241273668. [Diffusion Policy: Visuomotor Policy Learning via Action Diffusion](https://journals.sagepub.com/doi/full/10.1177/02783649241273668).
- Flow matching.

**Sep 17, Sep 22, and Oct 1 — Vision-Language-Action models**

- Yifan Zhong et al. (2025). arXiv:2507.01925. [A Survey on Vision-Language-Action Models: An Action Tokenization Perspective](https://arxiv.org/abs/2507.01925).

### October readings

**Oct 6 — Robot world models**

- Bohan Hou et al. (2026). *World Model for Robot Learning: A Comprehensive Survey*. arXiv:2605.00080.

**Oct 13 — Reinforcement Learning I and II**

- Jens Kober, J. Andrew Bagnell, and Jan Peters (2013). The International Journal of Robotics Research, 32(11), 1238–1274. MDP reading, around §2.1. [Reinforcement Learning in Robotics: A Survey](https://journals.sagepub.com/doi/full/10.1177/0278364913495721).
- Richard S. Sutton and Andrew G. Barto (2018). MIT Press. MDP reading, §3. Dynamic Programming reading, §§3–4. [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/RLbook2020.pdf).

**Oct 15 — Reinforcement Learning III and IV, and Inverse Reinforcement Learning I**

Inverse Reinforcement Learning I appears in the undated continuation at the top of PDF page 3.

- Richard S. Sutton and Andrew G. Barto (2018). MIT Press. Temporal Difference Learning reading, §§5–6. Function Approximation reading, §13. [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/RLbook2020.pdf).
- V. Mnih, K. Kavukcuoglu, D. Silver, et al. (2015). Nature, 518, 529–533. [Human-Level Control Through Deep Reinforcement Learning](https://www.nature.com/articles/nature14236#citeas).
- Brian D. Ziebart, Andrew L. Maas, J. Andrew Bagnell, and Anind K. Dey (2008). AAAI, vol. 8, pp. 1433–1438. [Maximum Entropy Inverse Reinforcement Learning](https://www.aaai.org/Papers/AAAI/2008/AAAI08-227.pdf).
- Chelsea Finn, Sergey Levine, and Pieter Abbeel (2016). ICML. [Guided Cost Learning: Deep Inverse Optimal Control via Policy Optimization](http://proceedings.mlr.press/v48/finn16.pdf).

### November readings

**Nov 3 — Perception**

- Tao Lin et al. (2026). arXiv:2605.14950. [Evo-Depth: A Lightweight Depth-Enhanced Vision-Language-Action Model](https://arxiv.org/abs/2605.14950).
- Daesol Cho et al. (2026). arXiv:2602.22461. [EgoAVFlow: Robot Policy Learning with Active Vision from Human Egocentric Videos via 3D Flow](https://arxiv.org/abs/2602.22461).

**Nov 5 — Vision-language-action models**

- Moo Jin Kim, Chelsea Finn, and Percy Liang (2025). Robotics: Science and Systems. [Fine-Tuning Vision-Language-Action Models: Optimizing Speed and Success](https://openvla-oft.github.io/).
- Yuhui Chen et al. (2025). Robotics: Science and Systems. [ConRFT: A Reinforced Fine-Tuning Method for VLA Models via Consistency Policy](https://arxiv.org/abs/2502.05450).

**Nov 10 — Vision-language-action models**

- Wenli Xiao et al. (2026). arXiv:2606.19980. [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](https://arxiv.org/abs/2606.19980).
- RLWRLD Team. [RLDX-1: A Dexterity-First Foundation Model for Robot Hands](https://www.rlwrld.ai/ko/rldx-1).

**Nov 12 — World models**

- Chenhao Li, Andreas Krause, and Marco Hutter (2025). arXiv:2501.10100. [Robotic World Model: A Neural Network Simulator for Robust Policy Optimization in Robotics](https://arxiv.org/abs/2501.10100).
- Pengfei Zhou et al. (2025). arXiv:2512.23541. [Act2Goal: From World Model to General Goal-Conditioned Policy](https://arxiv.org/abs/2512.23541).

**Nov 17 — Humanoid robots**

- Jonas Pai et al. (2025). arXiv:2512.15692. [mimic-video: Video-Action Models for Generalizable Robot Control Beyond VLAs](https://arxiv.org/abs/2512.15692).
- Lujie Yang et al. (2025). arXiv:2509.26633. [OmniRetarget: Interaction-Preserving Data Generation for Humanoid Whole-Body Loco-Manipulation and Scene Interaction](https://arxiv.org/abs/2509.26633).

**Nov 19 — Humanoid robots**

- Songlin Wei et al. (2026). arXiv:2603.12263. [Ψ₀: An Open Foundation Model Towards Universal Humanoid Loco-Manipulation](https://arxiv.org/abs/2603.12263).
- Xiaomeng Xu et al. (2026). arXiv:2603.03243. [HOMMI: Learning Whole-Body Mobile Manipulation from Human Demonstrations](https://arxiv.org/abs/2603.03243).

**Nov 24 — World models and other topics**

- Zhikai Zhang et al. (2025). arXiv:2509.13833. [Track Any Motions Under Any Disturbances](https://arxiv.org/abs/2509.13833).
- Chia-Yu Hung et al. (2025). arXiv:2511.14659. [NORA-1.5: A Vision-Language-Action Model Trained Using World Model- and Action-Based Preference Rewards](https://arxiv.org/pdf/2511.14659).

### December readings

**Dec 1 — Motion and task planning**

- Murtaza Dalal et al. (2024). arXiv:2409.05864. [Neural MP: A Generalist Neural Motion Planner](https://mihdalal.github.io/neuralmotionplanner/).
- Yufan Song et al. (2025). IEEE/RSJ IROS. [FCRF: Flexible Constructivism Reflection for Long-Horizon Robotic Task Planning with Large Language Models](https://arxiv.org/pdf/2507.14975).

**Dec 3 — Human-robot interaction**

- Zhanpeng He, Yifeng Cao, and Matei Ciocarlie (2025). arXiv:2503.01876. [Uncertainty Comes for Free: Human-in-the-Loop Policies with Diffusion Models](https://arxiv.org/abs/2503.01876).
- Akhil Padmanabha et al. (2026). Proceedings of the 21st ACM/IEEE International Conference on Human-Robot Interaction. [Waffle: A Wearable Approach to Bite Timing Estimation in Robot-Assisted Feeding](https://dl.acm.org/doi/abs/10.1145/3757279.3785560).

## Assignments and project

Students control simulated robots in Google Colab for the assignments. They may also use those robots for the final project.

- Complete each assignment individually and keep your code private.
- The course prohibits public publication of any provided class content, including on GitHub or a blog.
- Submit assignments by the due date for full credit. For each day late, the score is multiplied by 0.8. A submission two days late receives 64% of its original score. Submissions more than two days late receive zero.

| Submission requirement | Rule or penalty |
| --- | --- |
| Submission channel | Email submissions are prohibited. |
| Correct submission | The course allows no exceptions for submission mistakes. |
| PDF format | A submission in another format incurs a 20% penalty. |
| Code attachment | A missing code attachment incurs a 50% penalty. |
| Report language | Submit reports in English. Reports in other languages receive zero. |

## Paper presentations

Students take turns reviewing and presenting selected papers on recent advances and fundamentals in robot learning and interaction. Expect to present one or two papers over the semester. Choose a paper through the Google form and obtain the paper through the schedule links.

The presentation structure depends on the paper. The syllabus suggests covering the following.

1. State the problem.
2. Explain why it is important, hard, or valuable.
3. Explain the proposed solution.
4. Discuss advantages and disadvantages of the approaches cited in the paper.
5. Describe the paper's strengths.
6. Explain the experimental setup, if applicable.
7. Present major and minor comments.

Prepare about 45 minutes of presentation, followed by about 15–20 minutes of discussion and a quiz supplied by the presenter. The course records participation, quiz grades, and presentations when determining class participation scores.

## Course evaluation

| Component | Weight |
| --- | ---: |
| Assignments | 30% |
| Paper presentation and quiz | 30% |
| Midterm and final presentations and abstract paper | 30% |
| Class participation | 10% |

## Attendance

- Attendance is required and counts toward class participation.
- Missing three classes lowers the grade.
- If a missed lecture was delivered online, its recording will be posted on KLMS so students can review the material and submit any associated quiz.

## Additional reference links

The syllabus lists two additional links without titles after the References section.

- [arXiv:2404.09080](https://arxiv.org/pdf/2404.09080)
- [IEEE Xplore document 10933541](https://ieeexplore.ieee.org/document/10933541?denied=)
