# pylint: disable=no-member
# pylint: disable=too-many-arguments
# pylint: disable=too-many-public-methods
# pylint: disable=no-self-use

"""
Module containing the Case class
"""

import grpc

import rips.generated.Case_pb2 as Case_pb2
import rips.generated.Case_pb2_grpc as Case_pb2_grpc
import rips.generated.Commands_pb2 as Cmd
import rips.generated.Properties_pb2 as Properties_pb2
import rips.generated.Properties_pb2_grpc as Properties_pb2_grpc

from rips.grid import Grid
from rips.pdmobject import PdmObject
from rips.view import View

class Case(PdmObject):
    """ResInsight case class

    Operate on a ResInsight case specified by a Case Id integer.
    Not meant to be constructed separately but created by one of the following
    methods in Project: loadCase, case, allCases, selectedCasesq

    Attributes:
        id (int): Case Id corresponding to case Id in ResInsight project.
        name (str): Case name
        group_id (int): Case Group id
        chunkSize(int): The size of each chunk during value streaming.
                        A good chunk size is 64KiB = 65536B.
                        Meaning the ideal number of doubles would be 8192.
                        However we need overhead space, so the default is 8160.
                        This leaves 256B for overhead.
    """
    def __init__(self, channel, case_id):
        # Private properties
        self.__channel = channel
        self.__case_stub = Case_pb2_grpc.CaseStub(channel)
        self.__request = Case_pb2.CaseRequest(id=case_id)

        info = self.__case_stub.GetCaseInfo(self.__request)
        self.__properties_stub = Properties_pb2_grpc.PropertiesStub(
            self.__channel)
        PdmObject.__init__(self, self.__case_stub.GetPdmObject(self.__request),
                           self.__channel)

        # Public properties
        self.case_id = case_id
        self.name = info.name
        self.chunk_size = 8160

    def __grid_count(self):
        """Get number of grids in the case"""
        try:
            return self.__case_stub.GetGridCount(self.__request).count
        except grpc.RpcError as exception:
            if exception.code() == grpc.StatusCode.NOT_FOUND:
                return 0
            print("ERROR: ", exception)
            return 0

    def __generate_property_input_iterator(self, values_iterator, parameters):
        chunk = Properties_pb2.PropertyInputChunk()
        chunk.params.CopyFrom(parameters)
        yield chunk

        for values in values_iterator:
            valmsg = Properties_pb2.PropertyChunk(values=values)
            chunk.values.CopyFrom(valmsg)
            yield chunk

    def __generate_property_input_chunks(self, array, parameters):
        index = -1
        while index < len(array):
            chunk = Properties_pb2.PropertyInputChunk()
            if index is -1:
                chunk.params.CopyFrom(parameters)
                index += 1
            else:
                actual_chunk_size = min(len(array) - index + 1, self.chunk_size)
                chunk.values.CopyFrom(
                    Properties_pb2.PropertyChunk(values=array[index:index +
                                                              actual_chunk_size]))
                index += actual_chunk_size

            yield chunk
        # Final empty message to signal completion
        chunk = Properties_pb2.PropertyInputChunk()
        yield chunk

    def grid_path(self):
        """Get path of the current grid case

        Returns: path string
        """
        return self.get_value("CaseFileName")

    def grid(self, index):
        """Get Grid of a given index. Returns a rips Grid object

        Arguments:
            index (int): The grid index

        Returns: Grid object
        """
        return Grid(index, self, self.__channel)

    def grids(self):
        """Get a list of all rips Grid objects in the case"""
        grid_list = []
        for i in range(0, self.__grid_count()):
            grid_list.append(Grid(i, self, self.__channel))
        return grid_list

    def replace(self, new_grid_file):
        """Replace the current case grid with a new grid loaded from file

        Arguments:
            new_egrid_file (str): path to EGRID file
        """
        self._execute_command(replaceCase=Cmd.ReplaceCaseRequest(
            newGridFile=new_grid_file, caseId=self.case_id))
        self.__init__(self.__channel, self.case_id)

    def cell_count(self, porosity_model="MATRIX_MODEL"):
        """Get a cell count object containing number of active cells and
        total number of cells

        Arguments:
            porosity_model (str): String representing an enum.
                must be 'MATRIX_MODEL' or 'FRACTURE_MODEL'.
        Returns:
            Cell Count object with the following integer attributes:
                active_cell_count: number of active cells
                reservoir_cell_count: total number of reservoir cells
        """
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Case_pb2.CellInfoRequest(case_request=self.__request,
                                           porosity_model=porosity_model_enum)
        return self.__case_stub.GetCellCount(request)

    def cell_info_for_active_cells_async(self, porosity_model="MATRIX_MODEL"):
        """Get Stream of cell info objects for current case

        Arguments:
            porosity_model(str): String representing an enum.
                must be 'MATRIX_MODEL' or 'FRACTURE_MODEL'.

        Returns:
            Stream of **CellInfo** objects

        See cell_info_for_active_cells() for detalis on the **CellInfo** class.
        """
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Case_pb2.CellInfoRequest(case_request=self.__request,
                                           porosity_model=porosity_model_enum)
        return self.__case_stub.GetCellInfoForActiveCells(request)

    def cell_info_for_active_cells(self, porosity_model="MATRIX_MODEL"):
        """Get list of cell info objects for current case

        Arguments:
            porosity_model(str): String representing an enum.
                must be 'MATRIX_MODEL' or 'FRACTURE_MODEL'.

        Returns:
            List of **CellInfo** objects

        ### CellInfo class description

        Parameter                 | Description                                   | Type
        ------------------------- | --------------------------------------------- | -----
        grid_index                | Index to grid                                 | Integer
        parent_grid_index         | Index to parent grid                          | Integer
        coarsening_box_index      | Index to coarsening box                       | Integer
        local_ijk                 | Cell index in IJK directions of local grid    | Vec3i
        parent_ijk                | Cell index in IJK directions of parent grid   | Vec3i

        ### Vec3i class description

        Parameter        | Description                                  | Type
        ---------------- | -------------------------------------------- | -----
        i                | I grid index                                 | Integer
        j                | J grid index                                 | Integer
        k                | K grid index                                 | Integer

        """
        active_cell_info_chunks = self.cell_info_for_active_cells_async(
            porosity_model=porosity_model)
        received_active_cells = []
        for active_cell_chunk in active_cell_info_chunks:
            for active_cell in active_cell_chunk.data:
                received_active_cells.append(active_cell)
        return received_active_cells

    def time_steps(self):
        """Get a list containing all time steps

        The time steps are defined by the class **TimeStepDate** :

        Type      | Name
        --------- | ----------
        int       | year
        int       | month
        int       | day
        int       | hour
        int       | minute
        int       | second


        """
        return self.__case_stub.GetTimeSteps(self.__request).dates

    def days_since_start(self):
        """Get a list of decimal values representing days since the start of the simulation"""
        return self.__case_stub.GetDaysSinceStart(self.__request).day_decimals

    def views(self):
        """Get a list of views belonging to a case"""
        pdm_objects = self.children("ReservoirViews")
        view_list = []
        for pdm_object in pdm_objects:
            view_list.append(View(pdm_object))
        return view_list

    def view(self, view_id):
        """Get a particular view belonging to a case by providing view id
        Arguments:
            view_id(int): view id

        Returns: a view object

        """
        views = self.views()
        for view_object in views:
            if view_object.view_id == view_id:
                return view_object
        return None

    def create_view(self):
        """Create a new view in the current case"""
        return self.view(
            self._execute_command(createView=Cmd.CreateViewRequest(
                caseId=self.case_id)).createViewResult.viewId)

    def export_snapshots_of_all_views(self, prefix=""):
        """ Export snapshots for all views in the case

        Arguments:
            prefix (str): Exported file name prefix

        """
        return self._execute_command(
            exportSnapshots=Cmd.ExportSnapshotsRequest(
                type="VIEWS", prefix=prefix, caseId=self.case_id, viewId=-1))

    def export_well_path_completions(
            self,
            time_step,
            well_path_names,
            file_split,
            compdat_export="TRANSMISSIBILITIES",
            include_perforations=True,
            include_fishbones=True,
            fishbones_exclude_main_bore=True,
            combination_mode="INDIVIDUALLY",
    ):
        """
        Export well path completions for the current case to file

        Parameter                   | Description                                      | Type
        ----------------------------| ------------------------------------------------ | -----
        time_step                   | Time step to export for                          | Integer
        well_path_names             | List of well path names                          | List
        file_split                  | Split type:
                                     <ul>
                                     <li>'UNIFIED_FILE'</li>
                                     <li>'SPLIT_ON_WELL'</li>
                                     <li>'SPLIT_ON_WELL_AND_COMPLETION_TYPE'</li>
                                     </ul>                                             | String enum
        compdat_export              | Compdat export type:
                                      <ul>
                                      <li>'TRANSMISSIBILITIES'</li>
                                      <li>'WPIMULT_AND_DEFAULT_CONNECTION_FACTORS'</li>
                                      </ul>                                            | String enum
        include_perforations        | Export perforations?                             | bool
        include_fishbones           | Export fishbones?                                | bool
        fishbones_exclude_main_bore | Exclude main bore when exporting fishbones?      | bool
        combination_mode            | Combination mode:
                                      <ul>
                                      <li>'INDIVIDUALLY'</li>
                                      <li>'COMBINED'</li>
                                      </ul>                                            | String enum
        """
        if isinstance(well_path_names, str):
            well_path_names = [well_path_names]
        return self._execute_command(
            exportWellPathCompletions=Cmd.ExportWellPathCompRequest(
                caseId=self.case_id,
                timeStep=time_step,
                wellPathNames=well_path_names,
                fileSplit=file_split,
                compdatExport=compdat_export,
                includePerforations=include_perforations,
                includeFishbones=include_fishbones,
                excludeMainBoreForFishbones=fishbones_exclude_main_bore,
                combinationMode=combination_mode,
            ))

    def export_msw(self, well_path):
        """
        Export Eclipse Multi-segment-well model to file

        Arguments:
            well_path(str): Well path name
        """
        return self._execute_command(exportMsw=Cmd.ExportMswRequest(
            caseId=self.case_id, wellPath=well_path))

    def create_multiple_fractures(
            self,
            template_id,
            well_path_names,
            min_dist_from_well_td,
            max_fractures_per_well,
            top_layer,
            base_layer,
            spacing,
            action,
    ):
        """
        Create Multiple Fractures in one go

        Parameter              | Description                               | Type
        -----------------------| ----------------------------------       -| -----
        template_id            | Id of the template                        | Integer
        well_path_names        | List of well path names                   | List of Strings
        min_dist_from_well_td  | Minimum distance from well TD             | Double
        max_fractures_per_well | Max number of fractures per well          | Integer
        top_layer              | Top grid k-level for fractures            | Integer
        base_layer             | Base grid k-level for fractures           | Integer
        spacing                | Spacing between fractures                 | Double
        action                 | 'APPEND_FRACTURES' or 'REPLACE_FRACTURES' | String enum
        """
        if isinstance(well_path_names, str):
            well_path_names = [well_path_names]
        return self._execute_command(
            createMultipleFractures=Cmd.MultipleFracRequest(
                caseId=self.case_id,
                templateId=template_id,
                wellPathNames=well_path_names,
                minDistFromWellTd=min_dist_from_well_td,
                maxFracturesPerWell=max_fractures_per_well,
                topLayer=top_layer,
                baseLayer=base_layer,
                spacing=spacing,
                action=action,
            ))

    def create_lgr_for_completion(
            self,
            time_step,
            well_path_names,
            refinement_i,
            refinement_j,
            refinement_k,
            split_type,
    ):
        """
        Create a local grid refinement for the completions on the given well paths

        Parameter       | Description                            | Type
        --------------- | -------------------------------------- | -----
        time_steps      | Time step index                        | Integer
        well_path_names | List of well path names                | List of Strings
        refinement_i    | Refinment in x-direction               | Integer
        refinement_j    | Refinment in y-direction               | Integer
        refinement_k    | Refinment in z-direction               | Integer
        split_type      | Type of LGR split:
                          <ul>
                          <li>'LGR_PER_CELL'</li>
                          <li>'LGR_PER_COMPLETION'</li>
                          <li>'LGR_PER_WELL'</li>
                          </ul>                                  | String enum
        """
        if isinstance(well_path_names, str):
            well_path_names = [well_path_names]
        return self._execute_command(
            createLgrForCompletions=Cmd.CreateLgrForCompRequest(
                caseId=self.case_id,
                timeStep=time_step,
                wellPathNames=well_path_names,
                refinementI=refinement_i,
                refinementJ=refinement_j,
                refinementK=refinement_k,
                splitType=split_type,
            ))

    def create_saturation_pressure_plots(self):
        """
        Create saturation pressure plots for the current case
        """
        case_ids = [self.case_id]
        return self._execute_command(
            createSaturationPressurePlots=Cmd.CreateSatPressPlotRequest(
                caseIds=case_ids))

    def export_flow_characteristics(
            self,
            time_steps,
            injectors,
            producers,
            file_name,
            minimum_communication=0.0,
            aquifer_cell_threshold=0.1,
    ):
        """ Export Flow Characteristics data to text file in CSV format

        Parameter                 | Description                                   | Type
        ------------------------- | --------------------------------------------- | -----
        time_steps                | Time step indices                             | List of Integer
        injectors                 | Injector names                                | List of Strings
        producers                 | Producer names                                | List of Strings
        file_name                 | Export file name                              | Integer
        minimum_communication     | Minimum Communication, defaults to 0.0        | Integer
        aquifer_cell_threshold    | Aquifer Cell Threshold, defaults to 0.1       | Integer

        """
        if isinstance(time_steps, int):
            time_steps = [time_steps]
        if isinstance(injectors, str):
            injectors = [injectors]
        if isinstance(producers, str):
            producers = [producers]
        return self._execute_command(
            exportFlowCharacteristics=Cmd.ExportFlowInfoRequest(
                caseId=self.case_id,
                timeSteps=time_steps,
                injectors=injectors,
                producers=producers,
                fileName=file_name,
                minimumCommunication=minimum_communication,
                aquiferCellThreshold=aquifer_cell_threshold,
            ))

    def available_properties(self,
                             property_type,
                             porosity_model="MATRIX_MODEL"):
        """Get a list of available properties

        Arguments:
            property_type (str): string corresponding to property_type enum. Choices:
                - DYNAMIC_NATIVE
                - STATIC_NATIVE
                - SOURSIMRL
                - GENERATED
                - INPUT_PROPERTY
                - FORMATION_NAMES
                - FLOW_DIAGNOSTICS
                - INJECTION_FLOODING

            porosity_model(str): 'MATRIX_MODEL' or 'FRACTURE_MODEL'.
        """

        property_type_enum = Properties_pb2.PropertyType.Value(property_type)
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Properties_pb2.AvailablePropertiesRequest(
            case_request=self.__request,
            property_type=property_type_enum,
            porosity_model=porosity_model_enum,
        )
        return self.__properties_stub.GetAvailableProperties(
            request).property_names

    def active_cell_property_async(self,
                                   property_type,
                                   property_name,
                                   time_step,
                                   porosity_model="MATRIX_MODEL"):
        """Get a cell property for all active cells. Async, so returns an iterator

            Arguments:
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                porosity_model(str): string enum. See available()

            Returns:
                An iterator to a chunk object containing an array of double values
                Loop through the chunks and then the values within the chunk to get all values.
        """
        property_type_enum = Properties_pb2.PropertyType.Value(property_type)
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Properties_pb2.PropertyRequest(
            case_request=self.__request,
            property_type=property_type_enum,
            property_name=property_name,
            time_step=time_step,
            porosity_model=porosity_model_enum,
        )
        for chunk in self.__properties_stub.GetActiveCellProperty(request):
            yield chunk

    def active_cell_property(self,
                             property_type,
                             property_name,
                             time_step,
                             porosity_model="MATRIX_MODEL"):
        """Get a cell property for all active cells. Sync, so returns a list

            Arguments:
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                porosity_model(str): string enum. See available()

            Returns:
                A list containing double values
                Loop through the chunks and then the values within the chunk to get all values.
        """
        all_values = []
        generator = self.active_cell_property_async(property_type,
                                                    property_name, time_step,
                                                    porosity_model)
        for chunk in generator:
            for value in chunk.values:
                all_values.append(value)
        return all_values

    def grid_property_async(
            self,
            property_type,
            property_name,
            time_step,
            grid_index=0,
            porosity_model="MATRIX_MODEL",
    ):
        """Get a cell property for all grid cells. Async, so returns an iterator

            Arguments:
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                gridIndex(int): index to the grid we're getting values for
                porosity_model(str): string enum. See available()

            Returns:
                An iterator to a chunk object containing an array of double values
                Loop through the chunks and then the values within the chunk to get all values.
        """
        property_type_enum = Properties_pb2.PropertyType.Value(property_type)
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Properties_pb2.PropertyRequest(
            case_request=self.__request,
            property_type=property_type_enum,
            property_name=property_name,
            time_step=time_step,
            grid_index=grid_index,
            porosity_model=porosity_model_enum,
        )
        for chunk in self.__properties_stub.GetGridProperty(request):
            yield chunk

    def grid_property(
            self,
            property_type,
            property_name,
            time_step,
            grid_index=0,
            porosity_model="MATRIX_MODEL",
    ):
        """Get a cell property for all grid cells. Synchronous, so returns a list

            Arguments:
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                grid_index(int): index to the grid we're getting values for
                porosity_model(str): string enum. See available()

            Returns:
                A list of double values
        """
        all_values = []
        generator = self.grid_property_async(property_type, property_name,
                                             time_step, grid_index,
                                             porosity_model)
        for chunk in generator:
            for value in chunk.values:
                all_values.append(value)
        return all_values

    def set_active_cell_property_async(
            self,
            values_iterator,
            property_type,
            property_name,
            time_step,
            porosity_model="MATRIX_MODEL",
    ):
        """Set cell property for all active cells Async. Takes an iterator to the input values

            Arguments:
                values_iterator(iterator): an iterator to the properties to be set
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                porosity_model(str): string enum. See available()
        """
        property_type_enum = Properties_pb2.PropertyType.Value(property_type)
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Properties_pb2.PropertyRequest(
            case_request=self.__request,
            property_type=property_type_enum,
            property_name=property_name,
            time_step=time_step,
            porosity_model=porosity_model_enum,
        )

        request_iterator = self.__generate_property_input_iterator(
            values_iterator, request)
        self.__properties_stub.SetActiveCellProperty(request_iterator)

    def set_active_cell_property(
            self,
            values,
            property_type,
            property_name,
            time_step,
            porosity_model="MATRIX_MODEL",
    ):
        """Set a cell property for all active cells.

            Arguments:
                values(list): a list of double precision floating point numbers
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                porosity_model(str): string enum. See available()
        """
        property_type_enum = Properties_pb2.PropertyType.Value(property_type)
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Properties_pb2.PropertyRequest(
            case_request=self.__request,
            property_type=property_type_enum,
            property_name=property_name,
            time_step=time_step,
            porosity_model=porosity_model_enum,
        )
        request_iterator = self.__generate_property_input_chunks(
            values, request)
        reply = self.__properties_stub.SetActiveCellProperty(request_iterator)
        if reply.accepted_value_count < len(values):
            raise IndexError

    def set_grid_property(
            self,
            values,
            property_type,
            property_name,
            time_step,
            grid_index=0,
            porosity_model="MATRIX_MODEL",
    ):
        """Set a cell property for all grid cells.

            Arguments:
                values(list): a list of double precision floating point numbers
                property_type(str): string enum. See available()
                property_name(str): name of an Eclipse property
                time_step(int): the time step for which to get the property for
                grid_index(int): index to the grid we're setting values for
                porosity_model(str): string enum. See available()
        """
        property_type_enum = Properties_pb2.PropertyType.Value(property_type)
        porosity_model_enum = Case_pb2.PorosityModelType.Value(porosity_model)
        request = Properties_pb2.PropertyRequest(
            case_request=self.__request,
            property_type=property_type_enum,
            property_name=property_name,
            time_step=time_step,
            grid_index=grid_index,
            porosity_model=porosity_model_enum,
        )
        request_iterator = self.__generate_property_input_chunks(
            values, request)
        reply = self.__properties_stub.SetGridProperty(request_iterator)
        if reply.accepted_value_count < len(values):
            raise IndexError

    def export_property(
            self,
            time_step,
            property_name,
            eclipse_keyword=property,
            undefined_value=0.0,
            export_file=property,
    ):
        """ Export an Eclipse property

        Arguments:
            time_step (int): time step index
            property_name (str): property to export
            eclipse_keyword (str): Keyword used in export header. Defaults: value of property
            undefined_value (double):	Value to use for undefined values. Defaults to 0.0
            export_file (str):	File name for export. Defaults to the value of property parameter
        """
        return self._execute_command(exportProperty=Cmd.ExportPropertyRequest(
            caseId=self.case_id,
            timeStep=time_step,
            property=property_name,
            eclipseKeyword=eclipse_keyword,
            undefinedValue=undefined_value,
            exportFile=export_file,
        ))