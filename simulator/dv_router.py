"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics


# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter (basics.DVRouterBase):
  #NO_LOG = True # Set to True on an instance to disable its logging
  #POISON_MODE = True # Can override POISON_MODE here
  #DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

  def __init__ (self):
    """
    Called when the instance is initialized.

    You probably want to do some additional initialization here.
    """
    self.start_timer() # Starts calling handle_timer() at correct rate
    self.neighbors_distance = {}    # the router itself and hosts are not considered neighbors
    self.tables = {}                    # {port1:{dst1:x, dst2:y ...}, port2:{dst1:x, dst2:y ...} ...} hosts do not have entries
    self.dv = {self: (0, self)}         # {Dst: (distance, next_hop)}

  def handle_link_up (self, port, latency):
    """
    Called by the framework when a link attached to this Entity goes up.

    The port attached to the link and the link latency are passed in.
    """
    self.neighbors_distance[port] = latency


  def handle_link_down (self, port):
    """
    Called by the framework when a link attached to this Entity goes down.

    The port number used by the link is passed in.
    """
    self.neighbors_distance[port] = INFINITY
    self.tables[port].pop()
    for dst in self.dv:
      if self.dv[dst][1] == port:
        min_cost_to_dst = float("inf")
        next_hop = None
        for n in self.neighbors_distance:
          entries = self.tables[n]
          if dst in entries and min_cost_to_dst > entries[dst] + self.neighbors_distance[n]:
            min_cost_to_dst = entries[dst] + self.neighbors_distance[n]
            next_hop = self.neighbors_distance[n]
        self.dv[dst] = (min_cost_to_dst, next_hop)


  def handle_rx (self, packet, port):
    """
    Called by the framework when this Entity receives a packet.

    packet is a Packet (or subclass).
    port is the port number it arrived on.

    You definitely want to fill this in.
    """
    #self.log("RX %s on %s (%s)", packet, port, api.current_time())
    if isinstance(packet, basics.RoutePacket):
      # update table entries corresponding to the port
      # change the table entry for port to destination with cost as latency
      self.tables[port][packet.destination] = packet.latency
      # check for updates in self.dv
      min_cost_to_dst = self.dv[packet.destination][0]
      if packet.latency + neighbors_distance[port] < min_cost_to_dst:
        min_cost_to_dst = packet.latency + neighbors_distance[port]
        self.dv[packet.destination]= (min_cost_to_dst, port)
        # send RoutePacket packets to neighbors if self.dv updated
        for p in neighbors_distance:
          self.send(api.RoutePacket(destination, min_cost_to_dst), p)

    elif isinstance(packet, basics.HostDiscoveryPacket):
      latency = neighbors[port]
      self.neighbors_distance.pop(port)
      self.tables.pop(port)
      self.dv[packet.src] = (latency, port)
      for p in neighbors_distance:
        self.send(api.RoutePacket(packet.src, latency), p)

    else:
      self.send(packet, self.dv[packet.dst][1])

  def handle_timer (self):
    """
    Called periodically.

    When called, your router should send tables to neighbors.  It also might
    not be a bad place to check for whether any entries have expired.
    """
