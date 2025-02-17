#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

import json
import logging
import math
import time
from typing import Any, Tuple
import numpy as np
from scipy.spatial import distance_matrix

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        # ui.messageBox('Hello script')

        # cast the current product to a design project
        design = adsk.fusion.Design.cast(app.activeProduct)

        #create one component
        rootComp = design.rootComponent

        #create one sketch interface
        sketches = rootComp.sketches
        #use the contruction plane of the active component
        sketch = sketches.add(rootComp.xYConstructionPlane)

        #create square by lines
        sketchLines = sketch.sketchCurves.sketchLines 

        xArray = [-0.5, -0.5, 0.5, 0.5, -0.5]
        yArray = [-0.5, 0.5, 0.5, -0.5, -0.5]

        xArray = [-5, -5, 5, 5, -5]
        yArray = [-5, 5, 5, -5, -5]

        # xArray = [0, 0, 1, 1, 0]
        # yArray = [0, 1, 1, 0, 0]
        postArray = [0,1,2,3]

        # for i in postArray:
        #     startPoint = adsk.core.Point3D.create(xArray[i]/10,yArray[i]/10,0)
        #     endPoint = adsk.core.Point3D.create(xArray[i+1]/10,yArray[i+1]/10,0)
        #     sketchLines.addByTwoPoints(startPoint, endPoint)

        centPoint =  adsk.core.Point3D.create(0,0,0)
        # cornPoint =  adsk.core.Point3D.create(0.5,0.5,0)
        # sketchLines.addCenterPointRectangle(centPoint, cornPoint) 

        cornPoint = adsk.core.Point3D.create(1, 1, 0)
        sketchLines.addTwoPointRectangle(centPoint, cornPoint)

        const_Planes = adsk.fusion.ConstructionPlaneInput() 
        const_plane = const_Planes.setByOffset(rootComp.xYConstructionPlane,0.1) 
        circCenter = adsk.core.Point2D.create(1,1)
        adsk.core.


        
        '''
        circle_particles = CircleParticles(
            length      = 1,
            width       = 1,
            radius_mu   = 0.1,
            radius_std  = 0.01,
            vol_req     = 0.5,
            )
        fiber_positions = circle_particles.generate_microstructure(seed = 10)
        ui.messageBox(str(fiber_positions.shape[0]))
        # m = fiber_positions.reshape(20,1)
        # ui.messageBox(''.join(str(i) for i in m))
        ui.messageBox(str(fiber_positions[0,0]) + ',' + str(fiber_positions[0,1]))


        # fiber_positions.shape[0]

        for ii in range(1):

            circCenter = adsk.core.Point3D.create(fiber_positions[ii,0],fiber_positions[ii,1],0)
            sketchCirc = sketch.sketchCurves.sketchCircles
            sketchCirc.addByCenterRadius(circCenter, fiber_positions[ii,2])  
        '''      


    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class MicrostructureGenerator:
    "base class of mirostructure generator"

    def generate_microstructure(self, seed: Any = None) -> float:
        """generating micro-structure

        Parameters
        ----------
        seed : Any, optional
            seed generator or number , by default None
        """

        raise NotImplementedError("The function should be implemented \
                                  in sub-class \n")

    def plot_microstructure(
        self, save_figure: bool = False, fig_name: str = "RVE.png"
    ) -> None:
        """plot figure for RVE

        Parameters
        ----------
        save_figure : bool, optional
            save figure or not , by default False
        fig_name : str, optional
            figure name, by default "RVE.png"

        Raises
        ------
        NotImplementedError
            error report
        """

        raise NotImplementedError("The function should be implemented \
                                  in sub-class \n")

    def to_abaqus_format(self,
                         file_name: str = "micro_structure_info.json") -> None:
        """convert microstructure to abaqus format

        Parameters
        ----------
        file_name : str, optional
            file name, by default "micro_structure_info.json"

        Raises
        ------
        NotImplementedError
            error report
        """

        raise NotImplementedError("The function should be implemented \
                                  in sub-class \n")
    
class CircleParticles(MicrostructureGenerator):
    """2D RVE with different size of disks/circles

    Parameters
    ----------
    MicrostructureGenerator : class
        parent class of microstructure generator

    Examples
    --------
    >>> from rvesimulator.microstructure import CircleParticles
    >>> circle_particles = CircleParticles(
    ...     length=1,
    ...     width=1,
    ...     radius_mu=0.1,
    ...     radius_std=0.01,
    ...     vol_req=0.1,
    ... )
    >>> circle_particles.generate_microstructure()
    >>> circle_particles.plot_microstructure()
    >>> circle_particles.to_abaqus_format()
    >>> circle_particles.crate_rgmsh()
    """

    def __init__(
        self,
        length: float,
        width: float,
        radius_mu: float,
        radius_std: float,
        vol_req: float,
        num_guess_max: int = 50000,
        num_fiber_max: int = 750,
        num_cycle_max: int = 15,
        dist_min_factor: float = 1.1,
        stirring_iters: int = 100,
        print_log: bool = False,
    ) -> None:
        """Initialization

        Parameters
        ----------
        length : float
            length of RVE
        width : float
            width of RVE
        radius_mu : float
            mean of circle's radius
        radius_std : float
            std of circle's radius
        vol_req : float
            required volume fraction
        num_guess_max : int, optional
            maximum guess for fibers, by default 50000
        num_fiber_max : int, optional
            maximum fiber inside RVE, by default 750
        num_cycle_max : int, optional
            iteration cycles, by default 15
        dist_min_factor : float, optional
            distance factor, by default 2.07
        """
        # geometry information of the 2D RVE with homogeneous circles
        self.length = length
        self.width = width
        self.radius_mu = radius_mu
        self.radius_std = radius_std
        self.vol_req = vol_req
        self.print_log = print_log

        # Initialization of the algorithm
        self.dist_min_factor = dist_min_factor
        self.num_guess_max = num_guess_max
        self.num_fibers_max = num_fiber_max
        self.num_cycles_max = num_cycle_max
        self.stirring_iters = stirring_iters


    def _parameter_initialization(self) -> None:
        """Initialize the parameters"""
        self.num_change = 3
        self.num_cycle = 0
        self.vol_frac = 0
        self.vol_total = self.length * self.width

        # initial coordinate for position of fibre
        self.len_start = -1 * self.radius_mu
        self.len_end = self.length + self.radius_mu
        self.wid_start = -1 * self.radius_mu
        self.wid_end = self.width + self.radius_mu

        # fiber location is a nx4 numpy array x, y, r, p (partition)
        self.fiber_positions = None

    def generate_microstructure(
        self,
        seed: Any = None,
    ) -> None:
        """generate microstructure

        Parameters
        ----------
        seed : Any, optional
            seed number, by default None
        """

        # decide to use seed or not

        self.rng = np.random.default_rng(seed=seed)
        # counting time generating an RVE
        # logging.basicConfig(level=logging.INFO,
        #                     filename='rve_simulation.log', filemode='w')
        # self.logger = logging.getLogger("microstructure")
        # Create a buffer handler
        # self.logger.info("==================================================")
        # self.logger.info("Start generating microstructure")
        # self.logger.info(f"seed: {seed}")
        # self.logger.info(f"length: {self.length}")
        # self.logger.info(f"width: {self.width}")
        # self.logger.info(f"radius_mu: {self.radius_mu}")
        # self.logger.info(f"radius_std: {self.radius_std}")
        # self.logger.info(f"vol_req: {self.vol_req}")
        # start_time = time.time()
        self._parameter_initialization()
        self._procedure_initialization()
        self._core_iteration()
        # end_time = time.time()
        # self.time_usage = end_time - start_time
        # self.logger.info(f"time usage: {self.time_usage}")
        # self.logger.info("End generating microstructure")
        # self.logger.info("==================================================")
        # if self.print_log:
        #     file_handler = logging.FileHandler("microstructure.log")
        #     file_handler.setLevel(logging.INFO)
        #     # Create a logging format
        #     formatter = logging.Formatter(
        #         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        #     )
        #     file_handler.setFormatter(formatter)
        #     # Add the handlers to the logger
        #     self.logger.addHandler(file_handler)

        # # get microstructure info
        # self.microstructure_info = {
        #     "location_information": self.fiber_positions.tolist(),
        #     "radius_mu": self.radius_mu,
        #     "radius_std": self.radius_std,
        #     "len_start": self.len_start,
        #     "wid_start": self.wid_start,
        #     "len_end": self.len_end,
        #     "wid_end": self.wid_end,
        # }

        return self.fiber_positions


    def _procedure_initialization(self) -> None:
        """This function is used to generate the first disk and
        assign the initial values of the algorithm
        """

        # initialization(generate the first fiber randomly)
        self.fiber_min_dis_vector = np.zeros(
            (self.num_fibers_max, self.num_cycles_max + 1, 2)
        )
        self.num_fibers = 1
        # generate the location of the first fiber
        # the first fiber is generated with one partition
        print(self.radius_std)
        fiber_temp = self.generate_random_fibers(len_start=self.radius_mu, 
                                                 len_end=self.length - self.radius_mu,
                                                 wid_start=self.radius_mu,
                                                 wid_end=self.width - self.radius_mu,
                                                 radius_mu=self.radius_mu,
                                                 radius_std=0,
                                                 rng=self.rng,)
        # update the volume fraction information
        self.vol_frac = self.fiber_volume(self.radius_mu) / self.vol_total
        self.fiber_positions = np.zeros((1, 4))
        self.fiber_positions[0, 0:3] = fiber_temp.T
        self.fiber_positions[0, 3] = 1

    def _core_iteration(self) -> None:
        """core iteration part of the micro-structure generation method"""

        # the main loop of the algorithm
        while (
            self.vol_frac < self.vol_req
            and self.num_cycle < self.num_cycles_max
        ):
            # ================================================================#
            #                   generate the fibers randomly                  #
            # ================================================================#
            self.num_trial = 1
            while (
                self.num_trial < self.num_guess_max
                and self.vol_frac < self.vol_req
                and self.num_fibers < self.num_fibers_max
            ):
                # update the info of number trial
                self.num_trial = self.num_trial + 1
                fiber_temp = self.generate_random_fibers(
                    len_start=0,
                    len_end=self.length,
                    wid_start=0,
                    wid_end=self.width,
                    radius_mu=self.radius_mu,
                    radius_std=self.radius_std,
                    rng=self.rng,
                )
                # check the location of the fiber and
                new_fiber = self.new_positions(
                    x_center=fiber_temp[0, 0],
                    y_center=fiber_temp[1, 0],
                    radius=fiber_temp[2, 0],
                    length=self.length,
                    width=self.width,
                )
                if new_fiber[0, 3] == 4:
                    # self.logger.info("generate fiber, vertex check ...")
                    # if the temp fiber locates at un-proper location for mesh
                    while self.vertices_mesh_loc(new_fiber) == "fail":
                        fiber_temp = self.generate_random_fibers(
                            len_start=0,
                            len_end=self.length,
                            wid_start=0,
                            wid_end=self.width,
                            radius_mu=self.radius_mu,
                            radius_std=self.radius_std,
                            rng=self.rng,
                        )
                        new_fiber = self.new_positions(
                            x_center=fiber_temp[0, 0],
                            y_center=fiber_temp[1, 0],
                            radius=fiber_temp[2, 0],
                            length=self.length,
                            width=self.width,
                        )
                    # self.logger.info("generate fiber, vertex check pass")
                elif new_fiber[0, 3] == 2 or new_fiber[0, 3] == 1:
                    # self.logger.info("generate fiber, edge check ...")
                    # if the temp fiber locates at un-proper location for mesh
                    while self.proper_edge_mesh_location(new_fiber) == "fail":
                        fiber_temp = self.generate_random_fibers(
                            len_start=0,
                            len_end=self.length,
                            wid_start=0,
                            wid_end=self.width,
                            radius_mu=self.radius_mu,
                            radius_std=self.radius_std,
                            rng=self.rng,
                        )
                        new_fiber = self.new_positions(
                            x_center=fiber_temp[0, 0],
                            y_center=fiber_temp[1, 0],
                            radius=fiber_temp[2, 0],
                            length=self.length,
                            width=self.width,
                        )
                    # self.logger.info("generate fiber, edge check pass")
                # check the overlap of new fiber
                overlap_status = self.overlap_check(
                    new_fiber=new_fiber,
                    fiber_pos=self.fiber_positions.copy(),
                    dist_factor=self.dist_min_factor,
                )
                if overlap_status == 0:
                    self.fiber_positions = np.vstack(
                        (self.fiber_positions, new_fiber)
                    )
                    self.vol_frac = (
                        self.vol_frac
                        + self.fiber_volume(new_fiber[0, 2]) / self.vol_total
                    )
                    self.num_fibers = self.num_fibers + new_fiber.shape[0]
                del new_fiber

            # ================================================================#
            #                   stirring the fibers (first stage)             #
            # ================================================================#
            ii = 0
            if self.fiber_positions.shape[0] < self.num_fibers_max:
                # for every point, stirring is needed!
                while ii < self.fiber_positions.shape[0]:
                    (
                        self.fiber_min_dis_vector,
                        min_index,
                        min_dis,
                    ) = self.min_dis_index(
                        self.fiber_positions[ii, 0:2],
                        self.fiber_positions.copy(),
                        self.fiber_min_dis_vector,
                        ii,
                        self.num_cycle,
                    )
                    # generate the new fiber location
                    new_fiber_temp = self.gen_heuristic_fibers(
                        ref_point=self.fiber_positions[min_index, 0:3].copy(),
                        fiber_temp=self.fiber_positions[ii, 0:3].copy(),
                        dist_factor=self.dist_min_factor,
                        rng=self.rng,
                    )
                    # check the overlap of new fiber
                    new_fiber = self.new_positions(
                        x_center=new_fiber_temp[0, 0],
                        y_center=new_fiber_temp[0, 1],
                        radius=new_fiber_temp[0, 2],
                        length=self.length,
                        width=self.width,
                    )
                    # check proper location for mesh
                    # max stirring iteration
                    stirring_iter = 0
                    if new_fiber[0, 3] == 4:
                        # self.logger.info("stirring fiber,vertex check ...")
                        while (
                            self.vertices_mesh_loc(new_fiber) == "fail"
                            and stirring_iter < self.stirring_iters
                        ):
                            # generate new fiber
                            self.logger.info(f"iter: {stirring_iter}")
                            new_fiber_temp = self.gen_heuristic_fibers(
                                ref_point=self.fiber_positions[
                                    min_index, 0:3
                                ].copy(),
                                fiber_temp=self.fiber_positions[
                                    ii, 0:3].copy(),
                                dist_factor=self.dist_min_factor,
                                rng=self.rng,
                            )
                            # check the overlap of new fiber
                            new_fiber = self.new_positions(
                                x_center=new_fiber_temp[0, 0],
                                y_center=new_fiber_temp[0, 1],
                                radius=new_fiber_temp[0, 2],
                                length=self.length,
                                width=self.width,
                            )
                            stirring_iter += 1
                        if stirring_iter == self.stirring_iters:
                            self.logger.error(
                                "stirring vertex check failed")
                        # else:
                            # self.logger.info("stirring vertex check pass")
                    elif new_fiber[0, 3] == 2 or new_fiber[0, 3] == 1:
                        # self.logger.info("stirring fiber, edge check ...")
                        # check proper location for mesh
                        while self.proper_edge_mesh_location(
                            new_fiber
                        ) == "fail" and stirring_iter < self.stirring_iters:
                            # logger
                            # self.logger.info(f"iter: {stirring_iter}")
                            new_fiber_temp = self.gen_heuristic_fibers(
                                ref_point=self.fiber_positions[
                                    min_index, 0:3
                                ].copy(),
                                fiber_temp=self.fiber_positions[
                                    ii, 0:3].copy(),
                                dist_factor=self.dist_min_factor,
                                rng=self.rng,
                            )
                            # check the overlap of new fiber
                            new_fiber = self.new_positions(
                                x_center=new_fiber_temp[0, 0],
                                y_center=new_fiber_temp[0, 1],
                                radius=new_fiber_temp[0, 2],
                                length=self.length,
                                width=self.width,
                            )
                            stirring_iter += 1
                        # if stirring_iter == self.stirring_iters:
                        #     self.logger.error("stirring edge check failed")
                        # else:
                        #     self.logger.info("stirring edge check pass")
                    overlap_status = self.overlap_check(
                        new_fiber=new_fiber,
                        fiber_pos=self.fiber_positions.copy(),
                        dist_factor=self.dist_min_factor,
                        stage="step_two",
                        fiber_index=ii,
                    )
                    # check: if the new fibers(cause it maybe more than
                    # 1 fiber centers) will overlap with the
                    # remaining ones or not
                    if overlap_status == 0:
                        ii = self._update_fiber_position(
                            new_fiber=new_fiber, iter=ii
                        )
                    else:
                        ii = ii + int(self.fiber_positions[ii, 3])

                    del new_fiber, new_fiber_temp
            # end of one cycle
            self.num_cycle = self.num_cycle + 1

    def _update_fiber_position(self, new_fiber: np.ndarray, iter: int) -> int:
        """update the fiber position

        Parameters
        ----------
        new_fiber : np.ndarray
            the generated new fiber
        iter : int
            determine the nex fiber should be analysis

        Returns
        -------
        iter : int
            he updated number of index
        """
        # check the location compatibility
        if new_fiber[0, 3] != new_fiber.shape[0]:
            raise ValueError("fiber number compatibility issue")
        fiber_portion = int(self.fiber_positions[iter, 3].copy())
        self.fiber_positions = np.delete(
            self.fiber_positions,
            tuple(i + iter for i in range(fiber_portion)),
            axis=0,
        )
        self.fiber_positions = np.insert(
            self.fiber_positions, (iter), new_fiber, axis=0
        )
        iter = iter + int(new_fiber[0, 3])

        assert isinstance(iter, int) is True

        return iter

    def crate_rgmsh(self, num_discrete: int = 10) -> np.ndarray:
        """create rgmsh numpy array for crate

        Parameters
        ----------
        num_discrete : int, optional
            number of discrete partition, by default 10

        Returns
        -------
        np.ndarray
            2d numpy array that contains the micro-structure information
        """

        self.rgmsh = np.zeros((num_discrete, num_discrete))
        grid_len = self.length / num_discrete
        grid_wid = self.width / num_discrete
        radius = self.fiber_positions[:, 2].reshape(-1, 1)
        for ii in range(num_discrete):
            for jj in range(num_discrete):
                loc_temp = np.array(
                    [
                        [
                            self.length / (2 * num_discrete) + ii * grid_len,
                            self.width / (2 * num_discrete) + jj * grid_wid,
                        ]
                    ]
                )
                # distance measure
                points_dis_temp = distance_matrix(
                    self.fiber_positions[:, 0:2],
                    loc_temp,
                )

                if (points_dis_temp - radius).min() < 0:
                    self.rgmsh[ii, jj] = 1

        return self.rgmsh.T

    def vertices_mesh_loc(self, fiber: np.ndarray) -> int:
        """identify proper vertices location for meshing

        Parameters
        ----------
        fiber : np.ndarray
            temp fiber

        Returns
        -------
        int
            status of the fiber(0: improper, 1: proper)
        """
        # reformat the fiber location
        fiber = fiber.reshape((-1, 4))
        vertices = np.array([[0, 0],
                             [0, self.width],
                             [self.length, self.width],
                             [self.length, 0]])
        # calculate the distance between the fiber and the vertices
        points_dis_temp = distance_matrix(
            vertices,
            fiber[:, 0:2],
        )
        min_points_dis = points_dis_temp.min()
        if 0.0*fiber[0, 2] < min_points_dis < np.sqrt(2)*fiber[0, 2]:
            return "fail"
        else:
            return "pass"

    def proper_edge_mesh_location(self, fiber: np.ndarray) -> int:
        """identify proper edge location for meshing

        Parameters
        ----------
        fiber : np.ndarray
            temp fiber

        Returns
        -------
        int
            status of the fiber(0: improper, 1: proper)
        """
        # reformat the fiber location
        fiber = fiber.reshape((-1, 4))
        # for x edges
        dis_x = np.abs(np.array([fiber[:, 0], self.width - fiber[:, 0]]))
        if 0.80*fiber[0, 2] < dis_x.min() < fiber[0, 2]:
            return "fail"
        elif fiber[0, 2] < dis_x.min() < 1.2*fiber[0, 2]:
            return "fail"
        # for y edges
        dis_y = np.abs(np.array([fiber[:, 1], self.length - fiber[:, 1]]))
        if 0.8*fiber[0, 2] < dis_y.min() < fiber[0, 2]:
            return "fail"
        elif fiber[0, 2] < dis_y.min() < 1.2*fiber[0, 2]:
            return "fail"

        return "pass"

    def new_positions(
        self,
        x_center: float,
        y_center: float,
        radius: float,
        width: float,
        length: float,
    ) -> np.ndarray:
        """This is the function used to determine the locations of disks
        considering the boundary of RVE. To be specific, the disk should
        be divided into two parts or four parts if it is located in the
        outskirt area

        Parameters
        ----------
        x_center : float
            new center of X axis
        y_center : float
            new center of Y axis
        radius : float
            radius of the disk
        width : float
            width of RVE
        length : float
            length of RVE

        Returns
        -------
        np.ndarray
            XC, YC, split  which is the new locations of this fiber
            (because in some locations, the circles need to be split)
        ####################################
        #     #          2_2       #       #
        # 4_1 #                    #4_2    #
        ####################################
        #     #                    #       #
        # 2_3 #          1         #   2_4 #
        #     #                    #       #
        #     #                    #       #
        ####################################
        # 4_3 #         2_1        # 4_4   #
        #     #                    #       #
        ####################################

        """

        new_fiber = np.zeros((1, 4))
        if (
            radius <= x_center <= length - radius
            and radius <= y_center <= width - radius
        ):
            # locate in center region and split = 1
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 1)

        elif length - radius > x_center > radius > y_center:
            # location 2_1
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 2)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center, y_center + width, radius, 2]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif radius < x_center < length - radius and y_center > width - radius:
            # location 2_2
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 2)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center, y_center - width, radius, 2]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif width - radius > y_center > radius > x_center:
            # location 2_3
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 2)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center + length, y_center, radius, 2]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif radius < y_center < width - radius and x_center > length - radius:
            # location 2_4
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 2)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center - length, y_center, radius, 2]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif x_center < radius and y_center > width - radius:
            # location 4_1
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 4)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center + length, y_center, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array(
                        [x_center + length, y_center - width, radius, 4]
                    ).reshape((1, 4)),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center, y_center - width, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif x_center > length - radius and y_center > width - radius:
            # location 4_2
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 4)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center - length, y_center, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array(
                        [x_center - length, y_center - width, radius, 4]
                    ).reshape((1, 4)),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center, y_center - width, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif x_center < radius and y_center < radius:
            # location 4_3
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 4)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center + length, y_center, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array(
                        [x_center + length, y_center + width, radius, 4]
                    ).reshape((1, 4)),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center, y_center + width, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )

        elif x_center > length - radius and y_center < radius:
            # location 4_4
            new_fiber = self._first_new_fiber(x_center, y_center, radius, 4)
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center - length, y_center, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array(
                        [x_center - length, y_center + width, radius, 4]
                    ).reshape((1, 4)),
                )
            )
            new_fiber = np.vstack(
                (
                    new_fiber,
                    np.array([x_center, y_center + width, radius, 4]).reshape(
                        (1, 4)
                    ),
                )
            )

        else:
            raise Exception(
                "The location of the original point was wrong!!! \n"
            )

        return new_fiber

    def overlap_check(self,
        new_fiber: np.ndarray,
        fiber_pos: np.ndarray,
        dist_factor: float,
        fiber_index: int = 0,
        stage: str = "step_one",
    ) -> int:
        """overlap check between new fiber and the original ones

        Parameters
        ----------
        new_fiber : np.ndarray
            new fiber location
        fiber_pos : np.ndarray
            original fibers
        dist_factor : float
            distance factor which used to control the minimum distance
            between to fibers
        fiber_index : int, optional
            fiber index , by default 0
        stage : str, optional
            stage of the algorithm, by default "step_one"

        Returns
        -------
        int
            a flag number (1: overlap, 0: non-overlap)

        """

        fiber_pos = fiber_pos.copy()

        if stage == "step_one":
            min_dis_threshold = dist_factor * (
                new_fiber[0, 2] + fiber_pos[:, 2]
            ).reshape((-1, 1))
            points_dis_temp = distance_matrix(
                fiber_pos[:, 0:2], new_fiber[:, 0:2]
            )
            points_dis = np.min(points_dis_temp, 1, keepdims=True)
            min_dis = points_dis - min_dis_threshold

        elif stage == "step_two":
            # calculate the minimum distance threshold
            min_dis_threshold = dist_factor * (
                new_fiber[0, 2] + fiber_pos[:, 2]
            ).reshape((-1, 1))
            points_dis_temp = distance_matrix(
                fiber_pos[:, 0:2], new_fiber[:, 0:2]
            )
            points_dis_temp[
                fiber_index: fiber_index + int(fiber_pos[fiber_index, 3]), :
            ] = math.inf
            points_dis = np.min(points_dis_temp, 1, keepdims=True)
            min_dis = points_dis - min_dis_threshold

        else:
            raise ValueError(" Not defined stage \n")

        if min_dis.min() <= 0:
            status = 1
        else:
            status = 0

        return status

    def min_dis_index(self,
        temp_fiber: np.ndarray,
        fiber_pos: np.ndarray,
        fiber_min_dis_vector: np.ndarray,
        ii: int,
        cycle: int,
    ) -> Tuple[np.ndarray, int, float]:
        """This function is used to identify the index of closest fiber
        of every fiber, which is very import for the first heuristic
        stirring to get more space placing the new disks.

        Parameters
        ----------
        temp_fiber : np.ndarray
            the fiber been processed
        fiber_pos : np.ndarray
            fiber position
        fiber_min_dis_vector : np.ndarray
            the first column is the index of the closed point,
            the second column contains the minimum distance between
            those two points
        ii : int
            the index of the being processed point
        cycle : int
            the cycle of the algorithm. At different cycles, the
            criteria of identifying the closed point are  different.

        Returns
        -------
        fiber_min_dis_vector: np.ndarray
            The updated minimum distance array
        min_index: int
            The index of the minimum distance point
        min_dist : float
            The minimum distance to the minimum distance point

        """
        fiber_pos = fiber_pos.copy()

        # pre-process the data : find out the same row data and delete it
        temp_fiber = temp_fiber.reshape((1, 2))
        points_dis = distance_matrix(fiber_pos[:, 0:2], temp_fiber)
        points_dis[points_dis == 0] = math.inf
        if cycle == 0:
            min_dis = points_dis.min()
            min_index = np.where(points_dis == min_dis)[0]
            fiber_min_dis_vector[ii, cycle, 0] = min_index
            fiber_min_dis_vector[ii, cycle, 1] = min_dis
        elif cycle == 1:
            index_pre = int(fiber_min_dis_vector[ii, cycle - 1, 0])
            if index_pre < points_dis.shape[0]:
                points_dis[index_pre, :] = math.inf
            # identify the minimum index
            min_dis = points_dis.min()
            min_index = np.where(points_dis == min_dis)[0]
            fiber_min_dis_vector[ii, cycle, 0] = min_index
            fiber_min_dis_vector[ii, cycle, 1] = min_dis
        else:

            index_pre = int(fiber_min_dis_vector[ii, cycle - 1, 0])
            index_pre_pre = int(fiber_min_dis_vector[ii, cycle - 2, 0])
            if (
                index_pre < points_dis.shape[0]
                and index_pre_pre < points_dis.shape[0]
            ):
                points_dis[index_pre, :] = math.inf
                points_dis[index_pre_pre, :] = math.inf
            # identify the minimum index
            min_dis = points_dis.min()
            min_index = np.where(points_dis == min_dis)[0]
            fiber_min_dis_vector[ii, cycle, 0] = min_index
            fiber_min_dis_vector[ii, cycle, 1] = min_dis

        return fiber_min_dis_vector, min_index, min_dis

    def gen_heuristic_fibers(self,
        ref_point: np.ndarray,
        fiber_temp: np.ndarray,
        dist_factor: float,
        rng: Any,
    ) -> np.ndarray:
        """Move fiber to its reference point

        Parameters
        ----------
        ref_point : np.ndarray
            Reference point that the fiber should move to
        fiber_temp : np.ndarray
            The considering fiber
        dist_factor : float
            the minimum distance factor between two fibers
        rng: Any
            random generator

        Returns
        -------
        np.ndarray
            The updated location of the considering fiber
        """

        fiber_temp = fiber_temp.reshape((1, 3))
        ref_point = ref_point.reshape((1, 3))
        # generate the random factor for fiber stirring
        delta = rng.uniform(0, 1, 1)
        dist_min = dist_factor * (fiber_temp[0, 2] + ref_point[0, 2])
        fiber_loc = fiber_temp[0, 0:2].reshape((1, 2)).copy()
        ref_loc = ref_point[0, 0:2].reshape((1, 2)).copy()
        # maximum length of movement
        k = 1 - dist_min / distance_matrix(ref_loc, fiber_loc)
        fiber_temp[0, 0:2] = fiber_loc + delta * k * (ref_loc - fiber_loc)

        return fiber_temp

    def _first_new_fiber(self,x: float,
                         y: float,
                         r: float,
                         portion: int) -> np.ndarray:
        """generate the first new fiber

        Parameters
        ----------
        x : float
            x center
        y : float
            y center
        r : float
            radius
        portion : int
            portion of the fiber(1, 2, 4)

        Returns
        -------
        np.ndarray
            new fiber
        """
        return np.array([[x, y, r, portion]])


    def fiber_volume(self,radius: float) -> float:
        """calculate the fiber volume of the current fiber

        Parameters
        ----------
        radius : float
            radius

        Returns
        -------
        vol:float
            volume of current fiber(disk)
        """
        return np.pi * radius**2

    def generate_random_fibers(self,
        len_start: float,
        len_end: float,
        wid_start: float,
        wid_end: float,
        radius_mu: float,
        radius_std: float,
        rng,
    ) -> np.ndarray:
        """generate random fibers with different radiis

        Parameters
        ----------
        len_start : float
            the start location of length
        len_end : float
            the end location of length
        wid_start : float
            the start location of width
        wid_end : float
            the end location of width
        radius_mu : float
            mean of radius
        radius_std : float
            standard deviation of radius
        rng: any
            random seed or generator

        Returns
        -------
        np.ndarray
            location information of generated fiber
        """

        x = rng.uniform(len_start, len_end, 1)
        y = rng.uniform(wid_start, wid_end, 1)
        r = rng.normal(radius_mu, radius_std, 1)
        # the radius is too small for mesh
        while r <= 0.02*(len_end - len_start - 2*radius_mu):
            r = rng.normal(radius_mu, radius_std, 1)
        fiber = np.array([x, y, r])
        return fiber

