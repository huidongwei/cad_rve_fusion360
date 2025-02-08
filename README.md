# cad_rve_fusion360
Generate representative volume elements by python scripting in CAD software of Fusion360

### **Summary** ###

For the RVE for simulation of composite materials, the random spatial distribution must be generated by an iterative process, checking the volumetric ratio and the overlapping of particles in the matrix.

Fusion 360 provides the application programming interface (API) for parametric design where Python and C++ languages are allowed.

Python scripting is employed to generate circular particles through API of fusion 360 by the process shown below:

<p align="center">
    <img src="/res/figures/flow_chart.png" width="80%" align="center">
</p>

---
### **Result** ###

The generated RVE has a volumetric ratio of 50%, where the computational domain is  $`10mm \times 10mm`$  and particles has an average radius of 1mm with an deviation of 0.1mm, i.e., $`10\pm 0.1`$mm.
#```math
#SE = \frac{\sigma}{\sqrt{n}}
#```


<p align="center">
    <img src="/res/figures/RVE_image_001.png" width="100%" align="center">
</p>
