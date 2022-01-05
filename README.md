## 1. Data and method description
Python package to generate GML files in NHI HyDAMO format from a DAMO database. This can be used as input for the NHI HyDAMO database or D-Hydamo modelgenerator.

This toolbox is developed for Waterschap Vallei en Veluwe by Royal HaskoningDHV. 
It has been further improved for Waterschap Brabantse Delta. 

Free software: MIT License


## 2. Installation in anaconda
Save the `tohydamogml` folder on your hard disk. 
Open Anaconda prompt and navigate to the `tohydamogml` folder which contains the environment.yml file. 
Execute the following commands:

```
conda env create -f environment.yml
activate modelgenerator
```
The new python environment `modelgenerator` is created. Activate this environment each time you want to use the `tohydamogml` tool.

You can use the python package by adding the root folder of the package to the system path. In your python script you can add the folder with the following command:

`sys.path.append(r'path/to/tohydamogml')`


## 3. Usage
### Documentation
The usage is explained in a jupyter notebook.

Open Anaconda prompt, `activate` the modelworkflow environment and navigate to the 'parent' folder of the downloaded examples.
Start jupyter notebook with the following command:

`jupyter notebook`

navigate to `examples/wvv_notebook/Tutorial ToHyDAMOgml.ipynb`

Let's start!
 

## 4. Contributers
* jeroen.winkelhorst[@]rhdhv.com
* lisa.weijers[@]rhdhv.com
