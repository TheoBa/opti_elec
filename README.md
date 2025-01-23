# opti_elec
This repo host a PoC for building KPI in a home assistant app


# Modelisation thermique

## **Différents transferts thermiques**
<img src="readme/tt_home.png" alt="Differents transferts thermiques" width="400"/>

- La **conduction** ou **diffusion** : Le transfert d'énergie entre objets en contact physique.
- La **convection** : le transfert d'énergie entre un objet et son environnement, dû à un mouvement fluide 
- Le **rayonnement** : le transfert d'énergie par l'émission de rayonnement électromagnétique.

## Flux thermiques associés
`Conduction:`

<img src="https://latex.codecogs.com/svg.image?{\displaystyle\Phi&space;_{1\rightarrow&space;2}^{conduction}=\lambda\,S\,{\frac{T_{1}-T_{2}}{e}}={\frac{T_{1}-T_{2}}{R_{th}^{conduction}}}}" />


`Convection:` 

<img src="https://latex.codecogs.com/svg.image?{\displaystyle\Phi&space;_{1\rightarrow&space;2}^{convection}=h\,S\,(T_{1}-T_{2})={\frac{T_{1}-T_{2}}{R_{th}^{convection}}}" />

`Rayonnement:`

${\displaystyle \Phi^{\mathrm {ray}} =S\,\varepsilon \,\sigma \,T^{4}}$

## Expression générale du flux thermique
Par construction on peut relier le flux thermique à une quantité de chaleur échangée par unité de temps selon:

${\displaystyle \Phi ={\frac {\delta Q}{\mathrm {d} t}}={\dot {Q}}}$

Par ailleurs, la variation de quantité de chaleur échangée entre deux instants s'écrit:

${\displaystyle {\frac {\delta Q}{\mathrm {d} t}}=\rho \,c_{P}\,{\frac {\partial T}{\partial t}}=C\,{\frac {\partial T}{\partial t}}}$

**Hypothèses:** Le HomeModule est assimilé à un objet ponctuel homogène, si bien que les phénomènes internes de convections sont négligés.\
On omet volontairement la composante radiative des transferts thermiques dans un premier temps.\
Si bien que la combinaison des phénomènes convectifs et conductifs entre extérieur et intérieur en série se combinent si bien que 
<img src="https://latex.codecogs.com/svg.image?{\displaystyle{\Phi&space;_{1\rightarrow&space;2}^{TT}}={\frac{T_{ext}-T_{int}}{R_{th}}}}" />\
On considère ${\displaystyle {\mathcal {P}}}$, l'énergie produite au sein du logement typiquement par les radiateurs.

## Bilan énergétique
Le `bilan de puissance` donne:

<img src="https://latex.codecogs.com/svg.image?{\displaystyle{\Phi={\Phi&space;_{1\rightarrow&space;2}^{TT}}&plus;{\mathcal{P}}}\Leftrightarrow{C\,{\frac{\partial&space;T}{\partial&space;t}}={\frac{T_{ext}-T_{int}}{R_{\mathrm{th}}}&plus;{\mathcal{P}}}}\Leftrightarrow{{\frac{\partial&space;T}{\partial&space;t}}={\frac{T_{ext}-T_{int}}{R_{\mathrm{th}}C}}&plus;{\frac{\mathcal{P}}{C}}}}" />

Enfin:

<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{\frac{\partial&space;T_{int}}{\partial&space;t}}(t)&plus;{\frac{1}{\tau}}*T_{int}(t)={\frac{1}{\tau}}*T_{ext}&plus;{\frac{\mathcal{P}}{C}}}}(E)" />

Avec ${\displaystyle {\tau = R_{th}C}}$

<img src="https://latex.codecogs.com/svg.image?{\mathcal{P}}=\left\{\begin{matrix}{\mathcal{P}_{rad}}&{si}&{switch=ON}\\0&{sinon.}\\\end{matrix}\right." />

## Equations différentielles
$(E)$ donne alors:

`COOLING (switch = OFF)`
<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{\frac{\partial&space;T_{int}}{\partial&space;t}}(t)&plus;{\frac{1}{\tau}}*T_{int}(t)={\frac{1}{\tau}}*T_{ext}}}(1)" />

`HEATING (switch = ON)`
<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{\frac{\partial&space;T_{int}}{\partial&space;t}}(t)&plus;{\frac{1}{\tau}}*T_{int}(t)={\frac{1}{\tau}}*T_{ext}&plus;{\frac{\mathcal{P}}{C}}}}(2)" />

### Solutions
<img src="https://latex.codecogs.com/svg.image?(1)\Rightarrow{\boxed{\displaystyle{T_{int}=T_{ext}&plus;[T_{0}-T_{ext}]*e^{\frac{-t}{\tau}}}}}" />

<img src="https://latex.codecogs.com/svg.image?(2)\Rightarrow{\boxed{\displaystyle{T_{int}=T_{lim}&plus;[T_{0}-T_{lim}]*e^{\frac{-t}{\tau}}}}}" /> 

où: <img src="https://latex.codecogs.com/svg.image?T_{lim}=T_{ext}&plus;{\frac{\tau}{C}*{\mathcal{P}}}" />

### Pente à l'origine
<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{{\dot{T_{int}}}(0)=[T_{0}-T_{ext}]*{\frac{-1}{\tau}}}}}(1')" />

<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{{\dot{T_{int}}}(0)=[T_{0}-T_{ext}&plus;{\frac{\tau}{C}*{\mathcal{P}}}]*{\frac{-1}{\tau}}}}}(2')" />


### Derive thermal constants
<img src="https://latex.codecogs.com/svg.image?(1')\Rightarrow{\boxed{{\tau}=\frac{[T_{0}-T_{ext}]}{{-{\dot{T_{int}}}(0)}}}}" />

<img src="https://latex.codecogs.com/svg.image?(2')\Rightarrow{\boxed{\displaystyle&space;C={\frac{{\tau}*{\mathcal{P}}}{{\tau}*{\dot{T_{int}}}(0)&plus;T_{0}-T_{ext}}}}}" />
