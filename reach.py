import json
import sys
import igraph as ig
import queue

#$>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>$#

#FILTRO DE DATOS

# dict -> list
# Función que recibe un diccionario y retorna una tupla con los nodos que
# constituyen el contacto.
def get_nodes_parameters(uni_d):
  transmitter_node = uni_d["node1"].split("]")[0].split("[")[1]
  receiver_node = uni_d["node2"].split("]")[0].split("[")[1]
  start_connection = uni_d["start"]
  end_connection = uni_d["end"]
  final_dict = {"TRANSMITTER" : transmitter_node, "RECEIVER" : receiver_node, "START" : start_connection,
                 "END" : end_connection}
  return final_dict

# listof[dict] list[tuple] -> list[dict]
# Función que recibe una lista de diccionarios y una lista de tuplas, en que cada tupla
# corresponde 
def filter_fault(data,faults):
  new_data = []
  for unit_dict in data:
      parameters_list = get_nodes_parameters(unit_dict)
      t_node = parameters_list["TRANSMITTER"]
      r_node = parameters_list["RECEIVER"]
      change = False
      for fault in faults:
        if (t_node == fault[0] or r_node == fault[0]):
          if (fault[1] <= float(unit_dict["start"])):
              change = True 
          if (fault[1] > float(unit_dict["start"]) and fault[1] <= float(unit_dict["end"])):
            unit_dict["end"] = str(fault[1])
            new_data.append(unit_dict)
            change = True
        else:
          continue
      if change == False:
        new_data.append(unit_dict)
  return new_data

#$>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>$#

#%/////////////////////////////////////////////////////////////////////////////////////////////////////////%#

# Generacion de grafo

# listof[dict] -> List
# Funcion que recibe una lista de diccionarios y retorna una lista de strings con los nodos unicos.
def get_nodes_id(list_dict):
  nodos_unicos = []
  for dictionary in list_dict:
   if dictionary["TRANSMITTER"] not in nodos_unicos:
     nodos_unicos.append(dictionary["TRANSMITTER"])
   if dictionary["RECEIVER"] not in nodos_unicos:
     nodos_unicos.append(dictionary["RECEIVER"])
  return nodos_unicos

# Listof[dictionary] -> listof[lists]
# Funcion que recibe una lista de diccionarios y retorna una tupla que contiene una lista de diccionarios con cada vertice
# y una lista de diccionarios que contiene el nodo transmisor, receptor, inicio y fin de la conexion entre ambos nodos.
def graph_parameters(new_plan):
  new_format = []
  for dict in new_plan:
    new_dict = get_nodes_parameters(dict)
    new_format.append(new_dict)
  vertices = get_nodes_id(new_format)
  vertices_dict = []
  for vertice in vertices:
    vertices_dict.append({"name": vertice})
  edges = new_format
  return (vertices_dict,edges)

#%/////////////////////////////////////////////////////////////////////////////////////////////////////////%#

#-----------------------------------------------------------------------------------------------------------#
#BUSQUEDA DE NODOS ALCANZABLES

# List[dict] -> Dictionary
# Funcion que recibe una lista de diccionarios, en que cada uno corresponde al id del nodo de cada grafo, y retorna 
# un diccionario que contiene como llaves el id de cada nodo y como valor el numero de indice en el que se encuentra su lista
# con los ids de sus vertices adjacentes.
def get_adjacency_index_dict(dict_v):
  vertex_list = []
  for i in dict_v:
    vertex_list.append(i["name"])
  index = 0
  indexes_dict = dict()
  for j in vertex_list:
    indexes_dict.update({j: index})
    index += 1
  return indexes_dict

# List[list] ->List[list]
# Funcion que recibe una lista de listas, en que cada una corresponde a los vertices adjacentes a cada vertice. Estas contienen 0 en el caso
# de que no sea adjacente a cierto vertice, por lo que se eliminan los 0 asociados a la lista de cada vertice, retornando una lista de listas 
# con el filtro aplicado.
def remove_useless_adjacencies(adjacenciy_list):
  final_list = []
  for i in adjacenciy_list:
    count_0 = i.count(0)
    for j in range(count_0):
      i.remove(0)
    final_list.append(i)
  return final_list

# List[dict] String -> int
# Funcion que recibe una lista de diccionarios, el id del nodo y retorna el indice de la lista en donde se encuentra el diccionario asociado a 
# ese nodo. 
def get_node_index(l_d, id):
  index = 0
  length = len(l_d)
  while index < length:
    if (l_d[index]["name"] == id):
      break
    else:
      index += 1
  return index 

# list[igraph.edge] String String -> list[dict]
# Funcion que recibe una lista con objetos del tipo igraph.edge con todas las aristas de un vertice y el id asociado al nodo de destino,
# en caso de que no se ingrese nada retorna todas las aristas asociadas a ese vertice representadas por una lista de diccionarios en que 
# cada diccionario representa una arista entre el nodo fuente y el de destino, en caso contrario solo retorna las aristas asociadas al
# destino recibido
def get_edges(l_e, target = None, datatype = None):
  edge_list = []
  if datatype == "graph":
    for edge in l_e:
      if target == None:
        edge_list.append(edge.attributes())
      else:
        if edge.attributes()["RECEIVER"] == target:
          edge_list.append(edge.attributes())
  else:
    for edge in l_e:
      if target == None:
        edge_list.append(edge)
      else:
        if edge["RECEIVER"] == target:
          edge_list.append(edge)
  return edge_list

# List[dict] List[dict] -> List[dict]
# Recibe la lista de aristas del nodo padre hacia el nodo actual, todas las aristas del nodo actual y filtra estas ultimas eliminando
# aquellas que el inicio y el fin de su intervalo son menores que el tiempo de inicio para alguna arista del nodo padre.
def valid_edges(parent_edges, current_edges):
  if (len(current_edges) == 0):
    return parent_edges
  final_list = []
  for p_e in parent_edges:
    for c_e in current_edges:
      if c_e["START"] and float(c_e["END"]) < p_e["START"]:
        continue
      else:
        final_list.append(c_e)
  return final_list


def reachable_nodes(l_n):
  reachable_list = []
  for v in l_n:
    if v["visitado"] == True:
      reachable_list.append(v["name"])
  return reachable_list

# Graph String -> List[String]
# Funcion que recibe un grafo y un nodo(string) fuente desde el que queremos conocer todos los nodos que son alcanzables. 
def BFS(grafo,v_i,vertices):
  adjacency_list = remove_useless_adjacencies(grafo.get_adjacency(attribute = "RECEIVER"))
  adjacency_index_dict = get_adjacency_index_dict(vertices)
  #source_adjacencies = adjacency_list[adjacency_index_dict[v_i]]
  nodes = vertices
  for v in nodes:
    v.update({"visitado" : False})
    v.update({"padre" : None}) 
    v.update({"aristas_validas" : []})   
  source_index = get_node_index(nodes,v_i)
  nodes[source_index]["visitado"] = True
  #obtener todas las aristas
  p_v = grafo.vs[adjacency_index_dict[v_i]]
  edges_p = get_edges(p_v.out_edges(),None,"graph")
  nodes[source_index]["aristas_validas"] = edges_p
  fifo = queue.Queue()
  fifo.put(v_i)
  while fifo.empty() != True:
    p = fifo.get()
    adjacencies = adjacency_list[adjacency_index_dict[p]]
    for v in adjacencies:
      index = get_node_index(nodes,v)
      p_index = get_node_index(nodes,p)
      if (nodes[index]["visitado"] == False): #si no ha sido visitado
        # obtener todas las aristas del padre a v p_to_v_edges
        p_to_v_edges = get_edges(nodes[p_index]["aristas_validas"],v)
        # obtener todas las aristas de v v_edges
        v_v = grafo.vs[adjacency_index_dict[v]]
        v_edges = get_edges(v_v.out_edges(),None,"graph")
        # Combinacion entre p_to_v_edges y v_edges
        # Se eliminan aquellas combinaciones en que el inicio y el fin del intervalo en V es menor que el inicio de p 
        # Las que sobreviven se guardan en aristas validas
        final_edges = valid_edges(p_to_v_edges,v_edges)
        if (len(final_edges) == 0):
          continue
        nodes[index]["aristas_validas"] = final_edges
        # se guarda el padre
        nodes[index]["padre"] = p
        # se marca como visitado
        nodes[index]["visitado"] = True
        fifo.put(v)
  return nodes

#-----------------------------------------------------------------------------------------------------------#
# Simu methods

# List[dict] -> List[String]
# Se reciben los datos y se retornan los datos elegibles para inducir una falla.
def eligible_nodes(datos):
  partial_list = []
  final_list = []
  for i in datos:
      unique_node1 = i["node1"].split("]")[0].split("[")[1]
      unique_node2 = i["node2"].split("]")[0].split("[")[1]
      if "dsn-goldstone" not in i["node1"] and "dsn-tidbinbilla" not in i["node1"] and "dsn-madrid" not in i["node1"]:
        if "dsn-goldstone" not in i["node2"] and "dsn-tidbinbilla" not in i["node2"] and "dsn-madrid" not in i["node2"]:
          partial_list.append(unique_node1) 
          partial_list.append(unique_node2)
        else:
          partial_list.append(unique_node1)   
      else:
        if "dsn-goldstone" not in i["node2"] and "dsn-tidbinbilla" not in i["node2"] and "dsn-madrid" not in i["node2"]: 
          partial_list.append(unique_node2)
        else:
          continue
  for j in partial_list:
    if j not in final_list:
      final_list.append(j)
  return final_list

      
# List[dict] -> float
# Se reciben los datos y retorna el intervalo superior mas alto de los tiempos de existencia de las conexiones.
def maximum_time(d):
  maximum = 0
  for i in d:
    if float(i["end"]) > float(maximum):
      maximum = i["end"]
    else:
      continue
  return maximum
# List[dict] -> list[int]
# Retorna todos los nodos presentes en una lista de diccionarios.
def all_nodes(d):
  final_list = []
  for i in d:
    final_list.append(i["name"])
  return final_list
#---------------------------------------------------------------------------------------------------------------#

