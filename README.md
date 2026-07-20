<div align="center">

<img src="./assets/profile-header.svg" width="100%" alt="Michał Płaneta — Software Engineer" />

<br>

<a href="https://github.com/MichalPlanetaDev">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=18&duration=3000&pause=800&color=61DAFB&center=true&vCenter=true&width=900&lines=Systems%2C+game+technology%2C+security%2C+and+realtime+software;Deterministic+engineering%2C+CI%2FCD%2C+testing%2C+and+reproducible+delivery;Software+that+can+be+inspected%2C+explained%2C+and+maintained;Connecting+code%2C+graphics%2C+infrastructure%2C+and+hardware" alt="Engineering focus" />
</a>

<br>

[![GitHub](https://img.shields.io/badge/GitHub-MichalPlanetaDev-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MichalPlanetaDev)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Micha%C5%82_P%C5%82aneta-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/micha%C5%82-p%C5%82aneta-4b5701235)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:michalplanetabiznes@gmail.com)

<br>

![Location](https://img.shields.io/badge/Krak%C3%B3w%2C_Poland-334155?style=flat-square&logo=googlemaps&logoColor=white)
![Work](https://img.shields.io/badge/Open_to-Software_%26_Game_Engineering-0F766E?style=flat-square)
![Environment](https://img.shields.io/badge/Daily_environment-Ubuntu_%C2%B7_WSL_%C2%B7_CLI-5C2D91?style=flat-square&logo=linux&logoColor=white)
![Focus](https://img.shields.io/badge/Focus-C%2B%2B_%C2%B7_Systems_%C2%B7_Game_Tech_%C2%B7_Security-1D4ED8?style=flat-square)

</div>

---

<div align="center">

[Profile](#engineering-profile) · [Flagship Work](#flagship-engineering-work) · [Selected Work](#selected-work) · [Stack](#technology-stack) · [Approach](#engineering-approach) · [Live Metrics](#live-engineering-footprint) · [Contact](#contact)

</div>

---

<img src="./assets/profile.svg" width="100%" alt="Engineering Profile" />

## Engineering Profile

```text
michal@wsl:~$ whoami
Software engineer working across systems, game technology, security,
realtime graphics, tooling, backend services, and physical computing.

michal@wsl:~$ cat engineering-principles.txt
Correctness. Reproducibility. Explicit architecture. Measurable behaviour.
Clear documentation. Honest technical claims.
```

I am most engaged by projects that require participation across the complete engineering process rather than responsibility for one isolated layer. I want to understand how a system is designed, implemented, validated, measured, debugged, documented, and delivered, including the difficult parts involving algorithms, mathematics, physics, concurrency, rendering, simulation, data integrity, and performance.

This is why I identify primarily as a software engineer rather than through one narrowly defined technology. I work comfortably between low-level systems, game and rendering technology, web applications, backend services, automation, testing, infrastructure, data processing, electronics, and technical documentation. The objective is not to collect technologies, but to use the appropriate ones to build systems whose behaviour can be inspected and explained.

<table>
<tr>
<td width="25%" align="center"><b>Systems</b><br><sub>Deterministic runtimes, protocols, replay, persistence, concurrency, and performance.</sub></td>
<td width="25%" align="center"><b>Game Technology</b><br><sub>Gameplay systems, physics, rendering, tools, realtime interaction, audio, and content pipelines.</sub></td>
<td width="25%" align="center"><b>Security</b><br><sub>Trust boundaries, validation, evidence integrity, telemetry, investigation, and defensive design.</sub></td>
<td width="25%" align="center"><b>Delivery</b><br><sub>Linux workflows, CI/CD, automated tests, Docker, documentation, releases, and reproducible builds.</sub></td>
</tr>
</table>

---

<img src="./assets/projects.svg" width="100%" alt="Flagship Engineering Work" />

## Flagship Engineering Work

### Tickline

<div align="center">

<a href="https://github.com/MichalPlanetaDev/tickline">
  <img src="https://github-readme-stats.vercel.app/api/pin/?username=MichalPlanetaDev&repo=tickline&theme=tokyonight&hide_border=true&bg_color=070B16" width="70%" alt="Tickline repository" />
</a>

<br>

![Flagship](https://img.shields.io/badge/FLAGSHIP-DETERMINISTIC_SECURITY_ENGINEERING-7C3AED?style=for-the-badge)
![C++23](https://img.shields.io/badge/C%2B%2B-23-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)
![CI](https://img.shields.io/badge/CI-QUALITY_GATES-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

</div>

Tickline is a multi-language defensive engineering system built around an authoritative deterministic simulation. It accepts untrusted network-like input, performs bounded parsing and strict command validation, records accepted and rejected outcomes as canonical evidence, maintains a tamper-evident chain, persists verified investigations, reproduces behaviour through replay, exposes a read-only forensic workspace, and generates explainable analytics.

The repository is intentionally designed as one connected engineering system rather than a collection of unrelated demonstrations. Its C++23 runtime, Go developer console, Python analytics, SQLite investigation storage, Unity forensic viewer, Docker verification path, CI configuration, threat model, architecture documentation, and release process exist to demonstrate how responsibility moves through explicit trust boundaries.

<div align="center">

[![Repository](https://img.shields.io/badge/Open_Tickline-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MichalPlanetaDev/tickline)
[![Architecture](https://img.shields.io/badge/Read_architecture-0F766E?style=for-the-badge)](https://github.com/MichalPlanetaDev/tickline/blob/main/docs/architecture.md)
[![Threat Model](https://img.shields.io/badge/Threat_model-B91C1C?style=for-the-badge)](https://github.com/MichalPlanetaDev/tickline/blob/main/docs/threat-model.md)

</div>

<br>

<table>
<tr>
<td width="50%" valign="top">

### Rust Security Sandbox

A defensive multiplayer-security laboratory built around an authoritative Rust server, structured telemetry, evidence generation, SQLite-backed investigations, a read-only API, and a dashboard for reviewing suspicious sessions. It models findings as evidence rather than automatic punishment and keeps presentation, storage, validation, and investigation concerns separated.

<br>

[![Repository](https://img.shields.io/badge/Open_repository-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/MichalPlanetaDev/rust-security-sandbox)
![Rust](https://img.shields.io/badge/Rust-Authoritative_server-000000?style=flat-square&logo=rust&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Investigations-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Reproducible_demo-2496ED?style=flat-square&logo=docker&logoColor=white)

</td>
<td width="50%" valign="top">

### Anti-Cheat Portfolio

A focused Rust workspace demonstrating server-authoritative multiplayer simulation, client command validation, movement and fire-rate detection, packet-sequence validation, JSONL telemetry, offline replay, player-level risk summaries, CSV investigation export, Docker Compose, and a CLI-first Linux workflow.

<br>

[![Repository](https://img.shields.io/badge/Open_repository-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/MichalPlanetaDev/anticheat-portfolio)
![Rust](https://img.shields.io/badge/Rust-Workspace-000000?style=flat-square&logo=rust&logoColor=white)
![Telemetry](https://img.shields.io/badge/Telemetry-JSONL-475569?style=flat-square)
![CI](https://img.shields.io/badge/CI-Automated_checks-2088FF?style=flat-square&logo=githubactions&logoColor=white)

</td>
</tr>
</table>

---

## My Past Projects

<table>
<tr>
<td width="50%" valign="top">

### Space Invaders Adventure

A browser-based 3D space-combat project using Babylon.js and TypeScript, with WebGPU-to-WebGL fallback, six-degree-of-freedom flight, first-person and third-person cameras, component damage, weapon heat, enemy waves, boss encounters, cinematic transitions, and automated browser checks.

<br>

![Babylon.js](https://img.shields.io/badge/Babylon.js-Realtime_3D-BB464B?style=flat-square)
![WebGPU](https://img.shields.io/badge/WebGPU-GPU_API-005A9C?style=flat-square)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Testing-2EAD33?style=flat-square&logo=playwright&logoColor=white)

</td>
<td width="50%" valign="top">

### Signal Forge

An interactive oscilloscope and signal-analysis application focused on procedural visualization, readable technical controls, responsive UI, generated data, realtime presentation, and the relationship between signal parameters and their rendered representation.

<br>

![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Canvas](https://img.shields.io/badge/Canvas-Procedural_rendering-E34F26?style=flat-square&logo=html5&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Unity Game Collection

Academic and personal game projects covering platforming, arena survival, endless gameplay, tilemaps, physics, enemy behaviour, reusable gameplay systems, scene flow, UI, animation, audio, shaders, camera systems, and content integration.

<br>

![Unity](https://img.shields.io/badge/Unity-000000?style=flat-square&logo=unity&logoColor=white)
![C#](https://img.shields.io/badge/C%23-239120?style=flat-square&logo=csharp&logoColor=white)
![PhysX](https://img.shields.io/badge/PhysX-76B900?style=flat-square&logo=nvidia&logoColor=white)
![FMOD](https://img.shields.io/badge/FMOD-Interactive_audio-000000?style=flat-square)

</td>
<td width="50%" valign="top">

### Electronics and Physical Computing

Hands-on work with soldering, THT and PCB assembly, digital logic, timers, counters, seven-segment displays, light sensors, measurement, physical prototyping, and software-assisted acquisition and processing of data from real-world systems.

<br>

![Electronics](https://img.shields.io/badge/Electronics-Physical_computing-B91C1C?style=flat-square)
![Python](https://img.shields.io/badge/Python-Data_processing-3776AB?style=flat-square&logo=python&logoColor=white)
![Hardware](https://img.shields.io/badge/Hardware-Prototyping-475569?style=flat-square)
![IoT](https://img.shields.io/badge/IoT-Exploration-0F766E?style=flat-square)

</td>
</tr>
</table>

---

<img src="./assets/stack.svg" width="100%" alt="Technology Stack" />

## Technology Stack

The technologies below describe tools I have used in engineering, academic, research, or portfolio work. They are grouped by responsibility rather than presented as an unqualified proficiency ranking.

<div align="center">

### Languages and Runtime Work

<img src="https://skillicons.dev/icons?i=cpp,rust,cs,python,ts,js,java,go,bash,html,css&theme=dark&perline=11" alt="Programming languages" />

<br><br>

![SQL](https://img.shields.io/badge/SQL-Relational_data-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![WGSL](https://img.shields.io/badge/WGSL-GPU_shaders-5A45FF?style=for-the-badge)
![Markdown](https://img.shields.io/badge/Markdown-Technical_documentation-000000?style=for-the-badge&logo=markdown&logoColor=white)

### Game, Graphics, and Realtime Systems

<img src="https://skillicons.dev/icons?i=unity,unreal,blender&theme=dark&perline=6" alt="Game and graphics tools" />

<br><br>

![Babylon.js](https://img.shields.io/badge/Babylon.js-Realtime_3D-BB464B?style=for-the-badge)
![WebGL](https://img.shields.io/badge/WebGL-Rendering-990000?style=for-the-badge&logo=webgl&logoColor=white)
![WebGPU](https://img.shields.io/badge/WebGPU-Modern_GPU_API-005A9C?style=for-the-badge)
![PhysX](https://img.shields.io/badge/PhysX-Game_physics-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![Substance 3D Painter](https://img.shields.io/badge/Substance_3D_Painter-Texturing-1E1E1E?style=for-the-badge&logo=adobe&logoColor=white)
![FMOD](https://img.shields.io/badge/FMOD-Interactive_audio-000000?style=for-the-badge)
![Wwise](https://img.shields.io/badge/Wwise-Game_audio-00549F?style=for-the-badge)

### Applications, Backend, Data, and Automation

<img src="https://skillicons.dev/icons?i=react,nextjs,nodejs,vite,tailwind,sass,dotnet,fastapi,postgres,mysql,sqlite,pytorch,tensorflow,opencv&theme=dark&perline=14" alt="Application, backend, and data technologies" />

<br><br>

![REST](https://img.shields.io/badge/REST-API_design-02569B?style=for-the-badge)
![Playwright](https://img.shields.io/badge/Playwright-Browser_testing-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Numerical_computing-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)

### Systems, Tooling, and Delivery

<img src="https://skillicons.dev/icons?i=linux,ubuntu,windows,azure,git,github,docker,githubactions,cmake,npm,vscode,visualstudio,rider,pycharm&theme=dark&perline=14" alt="Systems and engineering tools" />

<br><br>

![WSL](https://img.shields.io/badge/WSL-Linux_on_Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![CLI](https://img.shields.io/badge/CLI-Terminal_first-111827?style=for-the-badge&logo=gnubash&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-Quality_gates-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

</div>

---

<img src="./assets/workflow.svg" width="100%" alt="Engineering Approach" />

## Engineering Approach

I prefer repositories that communicate their engineering decisions directly. A project should make its boundaries, assumptions, setup, validation strategy, failure modes, limitations, and operational workflow visible. The source code is only one part of that evidence.

<table>
<tr>
<td align="center" width="20%"><b>Linux first</b><br><sub>Ubuntu, WSL, Bash, terminal tooling, and reproducible commands.</sub></td>
<td align="center" width="20%"><b>Testable</b><br><sub>Unit, integration, browser, deterministic, and clean-install checks.</sub></td>
<td align="center" width="20%"><b>Reviewable</b><br><sub>Clear commits, explicit scope, architecture notes, and technical rationale.</sub></td>
<td align="center" width="20%"><b>Defensive</b><br><sub>Trust boundaries, bounded inputs, validation, evidence, and failure analysis.</sub></td>
<td align="center" width="20%"><b>Operational</b><br><sub>CI gates, releases, logs, debugging paths, and documented limitations.</sub></td>
</tr>
</table>

---

<img src="./assets/stats.svg" width="100%" alt="Live Engineering Footprint" />

## Live Engineering Footprint

The panel below is generated automatically from the repository workflow. It consolidates GitHub activity, language composition, engineering habits, achievements, recently played Spotify tracks, and Steam activity without repeating the same information through several unrelated third-party cards.

<div align="center">

<img src="./github-metrics.svg" width="100%" alt="Michał Płaneta — live GitHub, Spotify, and Steam metrics" />

</div>

<sub>Repository-language metrics describe the composition of public repositories. They are not a proficiency ranking. Spotify and Steam data reflect external account activity at the most recent workflow refresh.</sub>

---

<img src="./assets/contact.svg" width="100%" alt="Contact" />

## Contact

<div align="center">

I am interested in technically serious work where software must remain understandable, testable, reliable, and maintainable after the first successful demonstration. I am particularly drawn to roles that allow responsibility across several connected parts of a system rather than limiting engineering work to one repetitive layer.

<br><br>

[![LinkedIn](https://img.shields.io/badge/Connect_on_LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/micha%C5%82-p%C5%82aneta-4b5701235)
[![Email](https://img.shields.io/badge/Send_an_Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:michalplanetabiznes@gmail.com)
[![Repositories](https://img.shields.io/badge/Explore_repositories-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MichalPlanetaDev?tab=repositories)

<br><br>

<img src="https://komarev.com/ghpvc/?username=MichalPlanetaDev&label=Profile%20views&color=38bdf8&style=flat-square" alt="Profile view counter" />

<br><br>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24&height=120&section=footer" width="100%" alt="Profile footer" />

</div>
