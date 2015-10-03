"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics


# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter (basics.DVRouterBase):
  #NO_LOG = True # Set to True on an instance to disable its logging
  POISON_MODE = True # Can override POISON_MODE here
  #DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

  def __init__ (self):
    """
    Called when the instance is initialized.

    You probably want to do some additional initialization here.
    """
    self.start_timer()                  # Starts calling handle_timer() at correct rate
    self.tables = {}                    # {port1:{dest1:(x, start_time_1), dest2:(y, start_time_2) ...}, port2:{dest1:(x, start_time_3), dest1:(y, start_time_4) ...} ...}  dest is a host
    self.neighbors_distance = {}        # {port: latency}  the router itself and hosts are not considered neighbors; separating itself from self.dv for a better abstraction
    self.dv = {}                        # {dest: (distance, next_hop)}   dest is a host, next_hop is a port

  def handle_link_up (self, port, latency):
    """
    Called by the framework when a link attached to this Entity goes up.

    The port attached to the link and the link latency are passed in.
    """
    self.neighbors_distance[port] = latency
    self.tables[port] = {}
    # send the dictance vector to the new neighbor
    for dest in self.dv:
      send(basics.RoutePacket(dest, self.dv[dest][0]), port)


  def handle_link_down (self, port):
    """
    Called by the framework when a link attached to this Entity goes down.

    The port number used by the link is passed in.
    """
    # self.neighbors_distance[port] = INFINITY    #TO-DO: WTF??
    self.neighbors_distance.pop(port)
    self.tables.pop(port)
    for dest in self.dv:
      if self.dv[dest][1] == port:
        min_cost_to_dest = INFINITY
        next_hop = None
        for pp in self.neighbors_distance:
          entries = self.tables[pp]
          if dest in entries and min_cost_to_dest > entries[dest][0] + self.neighbors_distance[pp]:
            min_cost_to_dest = entries[dest][0] + self.neighbors_distance[pp]
            next_hop = pp
        if min_cost_to_dest == INFINITY:
          self.dv.pop(dest)
        else:
          self.dv[dest] = (min_cost_to_dest, next_hop)
        # event-based trigger; sending updated dv part
        for pp in self.neighbors_distance:
          if pp == next_hop:
            if POISON_MODE:
              self.send(basics.RoutePacket(dest, INFINITY), pp)
          else:
            self.send(basics.RoutePacket(dest, min_cost_to_dest), pp)


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
      self.tables[port][packet.destination] = (packet.latency + self.neighbors_distance[port], api.current_time())
      # check for updates in self.dv
      if packet.destination not in self.dv:
        self.dv[packet.destination] = (packet.latency + self.neighbors_distance[port], port)
        for p in self.neighbors_distance:
          if p == port:
            if POISON_MODE:
              self.send(basics.RoutePacket(packet.destination, INFINITY), p)
          else:
            self.send(basics.RoutePacket(packet.destination, packet.latency + self.neighbors_distance[port]), p)
      else:
        min_cost_to_dest = self.dv[packet.destination][0] if self.dv[packet.destination][1]!=port else self.neighbors_distance[port] + packet.latency
        if packet.latency + self.neighbors_distance[port] < min_cost_to_dest:
          min_cost_to_dest = packet.latency + self.neighbors_distance[port]

        # send RoutePacket packets to neighbors if self.dv updated
        if min_cost_to_dest != self.dv[packet.destination][0]:
          self.dv[packet.destination] = (min_cost_to_dest, port)
          for p in self.neighbors_distance:
            if p == port:
              if POISON_MODE:
                self.send(basics.RoutePacket(packet.destination, INFINITY), p)
            else:
              self.send(basics.RoutePacket(packet.destination, min_cost_to_dest), p)

    elif isinstance(packet, basics.HostDiscoveryPacket):
      latency = self.neighbors_distance[port]
      self.neighbors_distance.pop(port)   # this port directs to a host, no need to store in neighboring routers table
      self.tables[port] = {packet.src: (latency, api.current_time())}
      self.dv[packet.src] = (latency, port)
      for p in self.neighbors_distance:
        self.send(basics.RoutePacket(packet.src, latency), p)

    else:
      if packet.dst in self.dv:
        # do not forward a packet back to the port it arrived on
        if port != self.dv[packet.dst][1]:
          self.send(packet, self.dv[packet.dst][1])


  def handle_timer (self):
    """
    Called periodically.

    When called, your router should send tables to neighbors.  It also might
    not be a bad place to check for whether any entries have expired.
    """
    # handle expired routes
    for p in self.neighbors_distance:
      for dest in self.tables[p]:
        if api.current_time() - self.tables[p][dest][1] > 15:
          # an expired route
          self.tables[p][dest].pop()

          if self.dv[dest][1] == p:
            # recompute shortest path to dest
            min_cost_to_dest = INFINITY
            next_hop = None
            for pp in self.neighbors_distance:
              entries = self.tables[pp]
              if dest in entries and min_cost_to_dest > entries[dest][0] + self.neighbors_distance[pp]:
                min_cost_to_dest = entries[dest] + self.neighbors_distance[pp]
                next_hop = pp
            if min_cost_to_dest == INFINITY:
              self.dv.pop(dest)
            else:
              self.dv[dest] = (min_cost_to_dest, next_hop)

    # send my tables
    for pp in self.neighbors_distance:
      for dest in self.dv:
        if pp == self.dv[dest][1]:
          if POISON_MODE:
            self.send(basics.RoutePacket(packet.destination, INFINITY), pp)
        else:
          self.send(basics.RoutePacket(dest, self.dv[dest][0]), pp)