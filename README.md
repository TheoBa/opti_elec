# opti_elec
This repo host a PoC for building KPI in a home assistant app


# Modelisation thermique

## Historique du projet

L'ambition du projet a toujours été de modéliser la consommation électrique d'un logement en fonction de la température extérieure et de la température intérieure de la manière la plus simple possible.

La première itération naïve consistait à modéliser à 100% la consommation électrique. Nous supposions plusieurs hypothèses simplificatrices de manière à se placer dans le cadre théorique d'un transfert thermique conductif entre extérieur et intérieur avec un apport d'énergie constant, celui du système de chauffage.

Les premiers résultats obtenus étaient satisfaisant pour la preuve de concept mais manquaient de fiabilité pour une utilisation en production.

Finalement, alors qu'une approche 100% IA nous semblait inenvisageable en raison de la complexité du problème par rapport à la quantité et la qualité des données disponibles, nous avons opté pour une approche hybride.

Une modélisation thermique avec des hypothèses thermiques moins contraignantes - augmentant le nombre de degré de liberté du problème - augmentée par une démarche "type IA" avec l'introduction de variables optimisée lors d'une phase d'apprentissage.

Cette approche nous a non seulemement permis d'obtenir des résultats plus fiables mais surtout de mieux appréhender les différents phénomènes thermiques en jeu et d'éventuellement les ajouter dans la modélisation.

Quelques jours / semaines plus tard Adrien Caussanel m'a fait découvrir le site [reimagine-energy.ai](https://www.reimagine-energy.ai/p/data-driven-efficiency-predicting) qui théorise précisément l'approche hybride que j'avais retenue sans le savoir!
<img src="readme/graybox model.jpg" alt="Interest of grey-box model for thermal modeling" width="400"/>


## Les Différents transferts thermiques

- La **conduction** ou **diffusion** : Le transfert d'énergie entre objets en contact physique.
- La **convection** : le transfert d'énergie entre un objet et son environnement, dû à un mouvement fluide 
- Le **rayonnement** : le transfert d'énergie par l'émission de rayonnement électromagnétique. Dans notre modélisation, le seul phénomène radiatif pris en compte est le rayonnement perçu par le soleil.

## Flux thermiques associés
`Conduction:`

<img src="https://latex.codecogs.com/svg.image?{\displaystyle\Phi&space;_{1\rightarrow&space;2}^{conduction}=\lambda\,S\,{\frac{T_{1}-T_{2}}{e}}={\frac{T_{1}-T_{2}}{R_{th}^{conduction}}}}" />


`Convection:` 

<img src="https://latex.codecogs.com/svg.image?{\displaystyle\Phi&space;_{1\rightarrow&space;2}^{convection}=h\,S\,(T_{1}-T_{2})={\frac{T_{1}-T_{2}}{R_{th}^{convection}}}" />

`Rayonnement:`

${\displaystyle \Phi^{\mathrm {ray}} =S\,\varepsilon \,\sigma \,T^{4}}$ 


On omet la composante radiative des transferts thermiques dans un premier temps.\
Le flux thermique total est alors donné par la combinaison des phénomènes convectifs et conductifs entre extérieur et intérieur en série se combinent si bien que 
<img src="https://latex.codecogs.com/svg.image?{\displaystyle{\Phi&space;_{1\rightarrow&space;2}^{TT}}={\frac{T_{ext}-T_{int}}{R_{th}}}}" />

## **Les Différents transferts thermiques**

## Expression générale du flux thermique
Par construction on peut relier le `flux thermique` à une `variation de quantité de chaleur` échangée selon:

${\displaystyle \Phi ={\frac {\delta Q}{\delta t}}={\dot {Q}}}$

Par ailleurs, la variation de quantité de chaleur échangée entre deux instants s'écrit:

${\displaystyle {\frac {\delta Q}{\delta t}}=\rho \cdot c_{P} \cdot {\frac {\partial T}{\partial t}}=C \cdot {\frac {\partial T}{\partial t}}}$

## Puissances échangées
On considère ${\displaystyle {\mathcal {P_{tot}}}}$, la `puissance totale` échangée entre le module et l'extérieur.

On considère 3 sources de puissance échangée:
- La puissance fournie par les radiateurs lorsqu'ils sont allumés: ${\displaystyle {\mathcal {P_{heat}}}}$
- La puissance fournie par les radiations solaires: ${\displaystyle {\mathcal {P_{sun}}}}$
- La puissance échangée avec les modules thermiques adjacents: ${\displaystyle {\mathcal {P_{adj}}}}$

### Expressions des puissances
${\displaystyle {\mathcal {P_{heat}(t) = \delta_{switch}(t) \cdot \mathcal{P_{consigne}}}}}$

Avec la fonction indicatrice:
${\delta_{switch}(t)}=\left\{\begin{matrix}1&{si}&{switch=ON}\\0&{sinon.}\\\end{matrix}\right.$

${\displaystyle {\mathcal {P_{sun}(t)}}} = \alpha_{enso} \cdot \mathcal{P_{radiations}(t)}$

${\displaystyle {\mathcal {P_{adj}(t)}}} = P_{voisin} \cdot G(Text)$

Où $G(Text)$ est une `fonction de shaping` inversement proportionnelle à la température extérieure.

## Equation différentielle
Le `bilan de puissance` donne:

<img src="https://latex.codecogs.com/svg.image?{\displaystyle{\Phi={\Phi&space;_{1\rightarrow&space;2}^{TT}}&plus;{\mathcal{P}}}\Leftrightarrow{C\,{\frac{\partial&space;T}{\partial&space;t}}={\frac{T_{ext}-T_{int}}{R_{\mathrm{th}}}&plus;{\mathcal{P}}}}\Leftrightarrow{{\frac{\partial&space;T}{\partial&space;t}}={\frac{T_{ext}-T_{int}}{R_{\mathrm{th}}C}}&plus;{\frac{\mathcal{P}}{C}}}}" />

Enfin:

<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{\frac{\partial&space;T_{int}}{\partial&space;t}}(t)&plus;{\frac{1}{\tau}}*T_{int}(t)={\frac{1}{\tau}}*T_{ext}(t)&plus;{\frac{\mathcal{P}(t)}{C}}}}(E)" />

Avec ${\displaystyle {\tau = R_{th}C}}$

## Hypothèses et simplifications
Pour résoudre directement l'équation différentielle $(E)$ une bonne idée à priori serait de se débarasser des composantes temporelles présentes à la droite du signe égal.

Ainsi on pourrait se trouver dans le cas bien connu d'une équation différentielle linéaire du premier ordre à coefficients constants.


Le problème étant que les puissances définies ainsi que la température extérieure ne sont pas constantes dans le temps. `À moins que ?`

Les variations de ces termes sont lentes au cours du temps. Si bien que l'on peut les considérer `constantes par morceaux` en considérant des intervalles de temps suffisamment petits: on choisit 5 minutes

Sur un intervalle de temps donné, $(E)$ donne alors:

<img src="https://latex.codecogs.com/svg.image?{\boxed{\displaystyle{\frac{\partial&space;T_{int}}{\partial&space;t}}(t)&plus;{\frac{1}{\tau}}*T_{int}(t)={\frac{1}{\tau}}*T_{ext}&plus;{\frac{\mathcal{P}_{tot}}{C}}}}(1)" />

## Solutions
En prenant en compte les conditions initiales, les solutions de (E) en fonction de $\mathcal{P}$ sont:


<img src="https://latex.codecogs.com/svg.image?(1)\Rightarrow{\boxed{\displaystyle{T_{int}=T_{lim}&plus;[T_{0}-T_{lim}]*e^{\frac{-t}{\tau}}}}}" /> 

où: <img src="https://latex.codecogs.com/svg.image?T_{lim}=T_{ext}&plus;{\frac{\tau}{C}*[\delta_{switch}(t) \cdot {P_{consigne}}+ \alpha_{enso} \cdot {P_{radiations}(t) + G(T_{ext}) \cdot {P_{adj}]}" />


## Apprentissage
Pour l'instant - et c'est probablement amené à évoluer - on a paramétrisé la solution de l'équation différentielle par 5 paramètres:
- $R_{th}$
- $C$
- $\alpha_{enso}$
- $P_{adj}$
- $\delta t$ (le décalage temporel entre le moment où on allume le chauffage et le moment où la température commence à augmenter sur le capteur, une manière dissimulée de prendre en compte le phénomène de transport de chaleur au sein même du module thermique)

On définit ensuite une fonction de coût qui est la somme des carrés des erreurs entre les températures prédites et les températures réelles.

Puis on utilise ensuite une méthode de descente de gradient pour minimiser cette fonction de coût et en déduire les paramètres associés.
