#-----------------------------------------------------------------------------------------
# Scurve.py
#
# Smoothly move to a target with limits on velocity and acceleration.
# Ok to change target at any time.
# Do not change max velocity or max acceleration when running, that makes a discontinuity
#
# DrTomFlint 19 Sept 2023
#-----------------------------------------------------------------------------------------
class Scurve:
    def __init__(self,target,x0=0,v0=0,vmax=1,amax=1):
        self.target=target
        self.x=x0
        self.v=v0
        self.vmax=vmax
        self.amax=amax
        self.delta=target-x0
        self.done=amax
        self.stop=0

    def step(self):
        "advance one step toward target"

        self.delta = self.target-self.x

        if abs(self.delta)<self.done:
            # close enough to target to be done
            self.x=self.target
            self.v=0
        else:
            # update velocity
            if self.delta>0:
                # should move in plus direction
                if self.v<0:
                    # wrong direction accelerate at amax
                    self.v+=self.amax
                    if self.v>self.vmax:
                        self.v=self.vmax
                else:
                    # correct direction, check if within stopping distance
                    self.stop=self.v*self.v/(2*self.amax)+1*self.v
                    self.stop*=1.05
                    if self.delta<self.stop:
                        # within stopping distance, slow down
                        self.v-=self.amax
                    else:
                        # not within stopping distance, accelerate to vmax
                        self.v+=self.amax
                        if self.v>self.vmax:
                            self.v=self.vmax
            else:
                # should move in minus direction
                if self.v>0:
                    # wrong direction
                    self.v-=self.amax
                    if self.v<-self.vmax:
                        self.v=-self.vmax
                else:
                    # correct direction, check if within stopping distance
                    self.stop=-(self.v*self.v/(2*self.amax)+1*self.v)
                    self.stop*=1.05
                    if self.delta>self.stop:
                        # within stopping distance, slow down
                        self.v+=self.amax
                    else:
                        # not within stopping distance, accelerate to vmax
                        self.v-=self.amax
                        if self.v<-self.vmax:
                            self.v=-self.vmax
        
        # update position
        self.x+=self.v
        return self.x

#-----------------------------------------------------------------------------------------
