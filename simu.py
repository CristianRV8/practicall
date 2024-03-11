import reach as rn
import sys
import igraph as ig
import random
import json

# FLUJO
#List[dict] int -> tuple
# Función que recibe los datos y el nodo de inicio. A partir de estos
# se induce una falla de forma aleatoria y retorna una tupla con los 
# datos filtrados a partir de dicha falla y los nodos que son alcanzables.
def all_simu(data,start_node):
  ##Lista de los nodos a los cuales es posible inducir falla
  selectable_nodes = rn.eligible_nodes(data)
  if str(start_node) in selectable_nodes:
   selectable_nodes.remove(str(start_node))
  ##intervalo de tiempo en el cual existe la red
  max_time = rn.maximum_time(data)
  #elegir un nodo aleatorio
  random_node_index = random.randint(0,len(selectable_nodes)-1)
  ##elegimos un intervalo aleatorio
  random_time = random.uniform(0.0, float(max_time))
  print("Falla en nodo",selectable_nodes[random_node_index],"en el tiempo", random_time,"\n")
  datos_filtrados = rn.filter_fault(data, [(selectable_nodes[random_node_index],random_time)])
  vertices, aristas =  rn.graph_parameters(datos_filtrados)
  g = ig.Graph.DictList(vertices,aristas,directed=True,edge_foreign_keys = ("TRANSMITTER","RECEIVER"))
  v_nodes = rn.reachable_nodes(rn.BFS(g,start_node,vertices))
  return (datos_filtrados, v_nodes)

std_in = sys.argv
file_name = std_in[1]
with open(file_name) as file:
    data = json.load(file)
eligible = rn.eligible_nodes(data)
print("Nodos elegibles:",rn.all_nodes(rn.graph_parameters(data)[0]))
start_node = input("nodo inicial? ")
n_initial_nodes = len(eligible) + 3 
n_current_nodes = n_initial_nodes
while(n_current_nodes >= n_initial_nodes/2):
  data_nodes = all_simu(data,start_node)
  data = data_nodes[0]
  nodes = data_nodes[1]
  n_current_nodes = len(nodes)
  print("Es posible llegar a:",nodes,"desde",start_node,"\n")