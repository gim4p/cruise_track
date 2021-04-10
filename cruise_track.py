# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CruiseTrackExport
                                 A QGIS plugin
 Just shall export waypoints for cruise track.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-04-01
        git sha              : $Format:%H$
        copyright            : (C) 2021 by gia
        email                : schokulele@yahoo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog  # added
from qgis.core import QgsProject, Qgis  # added

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .cruise_track_dialog import CruiseTrackExportDialog
import os.path


class CruiseTrackExport:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CruiseTrackExport_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Cruise Track Export')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CruiseTrackExport', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu,action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/cruise_track/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Cruise Track Export'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Cruise Track Export'), action)
            self.iface.removeToolBarIcon(action)

    def select_output_file(self):  # added
        filename, _filter = QFileDialog.getSaveFileName(self.dlg, "Select   output file ", "", '*.cvt')
        self.dlg.le_outTrack.setText(filename)

    def run(self):
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = CruiseTrackExportDialog()
            self.dlg.tb_outTrack.clicked.connect(self.select_output_file)

        layers = QgsProject.instance().layerTreeRoot().children()  # Fetch the currently loaded layers
        self.dlg.cb_inVector.clear()  # Clear the contents of the comboBox from previous runs
        self.dlg.cb_inVector.addItems([layer.name() for layer in layers])  # Populate the comboBox with names of all the loaded layers

        self.dlg.show()  # show the dialog
        result = self.dlg.exec_()  # Run the dialog event loop
        if result:  ######## PyQgis start ########

            from statistics import mean, median, mode, stdev
            import numpy as np
            import numpy.matlib
            import pandas as pd
            import os
            import sys
            from qgis.utils import iface
            from qgis.core import QgsPointXY, QgsFeatureRequest, QgsField, QgsWkbTypes
            from PyQt5.QtCore import QVariant
            from datetime import datetime
            import matplotlib.pyplot as plt
            import localsolver
            import pyproj
            from pyproj import Proj
            import math

            #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
            selectedLayerIndex = self.dlg.cb_inVector.currentIndex()   # Identify selected layer by its index
            ly_tree_nd = layers[selectedLayerIndex]
            laye_r = ly_tree_nd.layer() # Gives you the layer you have selected in the Layers Panel
            laye_r.dataProvider().deleteAttributes(list(range(0, len(laye_r.fields().names()))))  # safer and easier to just delete attribute table (change maybe later)
            laye_r.updateFields()
            layer_provider = laye_r.dataProvider()
            
            #### what input layer
            for fea_t in laye_r.getFeatures():
                geom = fea_t.geometry()
                if geom.type() == QgsWkbTypes.PointGeometry:
                    Point_MPoint_Line = 0 # Point (distinction to Multipoint still missing)
                elif geom.type() == QgsWkbTypes.LineGeometry:
                    Point_MPoint_Line = 1 # Line
            
            if Point_MPoint_Line==1:
                field_name = "X_start"  # if there are the right fields still missing, make them
                field_index = laye_r.fields().indexFromName(field_name)
                if field_index == -1:
                    layer_provider.addAttributes([QgsField("X_start", QVariant.Double),
                                                  QgsField("X_stop", QVariant.Double), QgsField("Y_start", QVariant.Double),
                                                  QgsField("Y_stop", QVariant.Double), QgsField("length", QVariant.Double),
                                                  QgsField("X_mean", QVariant.Double)])
                    laye_r.updateFields()

                #### put data from shapefile into attribute table
                laye_r.startEditing()
                for fea_t in laye_r.getFeatures():
                    geom = fea_t.geometry().asMultiPolyline()
                    for line in geom:
                        start_point = QgsPointXY(geom[0][0])
                        end_point = QgsPointXY(geom[-1][-1])
                        fea_t["X_start"] = start_point[0]
                        fea_t["X_stop"] = end_point[0]
                        fea_t["Y_start"] = start_point[1]
                        fea_t["Y_stop"] = end_point[1]
                        fea_t["length"] = fea_t.geometry().length()  # ellipsoid; noch nicht herausgefunden, wie man das umstellt (trotz geänderter Projektion)
                        if ((abs(start_point.azimuth(end_point)) > 45) and (abs(start_point.azimuth(end_point)) < 125)):
                            fea_t["X_mean"] = median([start_point[1], end_point[1]])
                        else:
                            fea_t["X_mean"] = median([start_point[0], end_point[0]])
                        laye_r.updateFeature(fea_t)
                laye_r.commitChanges()
                df = pd.DataFrame(fea_t.attributes() for fea_t in laye_r.getFeatures(QgsFeatureRequest()))

                #### #### #### #### if CheckBox 'accessory' active  #### #### #### #### #### #### #### #### #### #### #### ####
                if self.dlg.accessory.isChecked():
                    #### wenn chaotische linienreihenfolge -> organise by X_mean/Y-mean (nur, wenn Profile nicht sehr divers in Länge und Posiion)
                    df = df.sort_values(by=[5])
                    #### alle Linien gleich ausrichten
                    new_lon_st = np.zeros(len(df))
                    new_lon_sp = np.zeros(len(df))
                    new_lat_st = np.zeros(len(df))
                    new_lat_sp = np.zeros(len(df))
                    for nn in list(range(0, len(df))):
                        if df.iloc[nn, 0] < df.iloc[nn, 1]:
                            new_lon_st[nn] = df.iloc[nn, 0]
                            new_lon_sp[nn] = df.iloc[nn, 1]
                            new_lat_st[nn] = df.iloc[nn, 2]
                            new_lat_sp[nn] = df.iloc[nn, 3]
                        else:
                            new_lon_st[nn] = df.iloc[nn, 1]
                            new_lon_sp[nn] = df.iloc[nn, 0]
                            new_lat_st[nn] = df.iloc[nn, 3]
                            new_lat_sp[nn] = df.iloc[nn, 2]
                    arrays = np.transpose([new_lon_st, new_lon_sp, new_lat_st, new_lat_sp])
                    df = pd.DataFrame(arrays)

                    #### flip NS
                    if self.dlg.checkBox_flipNS.isChecked():
                        df = df.iloc[::-1]  # NS

                    #### series for normal profile
                    if self.dlg.normalProfiles.isChecked():
                        #### flip WE
                        if self.dlg.checkBox_flipWE.isChecked():
                            idx_reihe = -1 + np.sort(np.matlib.repmat(np.arange(0, len(laye_r) * 2, 4).tolist(), 1, 4)) + np.matlib.repmat((2, 1, 3, 4), 1, len(np.arange(0, len(laye_r) * 2, 4).tolist()))
                        else:
                            idx_reihe = -1 + np.sort(np.matlib.repmat(np.arange(0, len(laye_r) * 2, 4).tolist(), 1, 4)) + np.matlib.repmat((1, 2, 4, 3), 1, len(np.arange(0, len(laye_r) * 2, 4).tolist()))
                        idx_reihe = idx_reihe[0][:]
                        idx_reihe = idx_reihe[0:len(df) * 2]

                    #### series for every 2nd line
                    elif self.dlg.every2nd.isChecked():
                        reihe_hin = np.arange(0, len(laye_r), 2).tolist()
                        reihe_her = np.arange(1, len(laye_r), 2).tolist()
                        lon_st_hin = np.zeros(len(reihe_hin))
                        lon_sp_hin = np.zeros(len(reihe_hin))
                        lat_st_hin = np.zeros(len(reihe_hin))
                        lat_sp_hin = np.zeros(len(reihe_hin))
                        lon_st_her = np.zeros(len(reihe_her))
                        lon_sp_her = np.zeros(len(reihe_her))
                        lat_st_her = np.zeros(len(reihe_her))
                        lat_sp_her = np.zeros(len(reihe_her))
                        for nn in range(0, len(reihe_hin)):                 # there
                            if nn / 2 != np.round(nn / 2):
                                lon_st_hin[nn] = df.iloc[reihe_hin[nn], 0]
                                lon_sp_hin[nn] = df.iloc[reihe_hin[nn], 1]
                                lat_st_hin[nn] = df.iloc[reihe_hin[nn], 2]
                                lat_sp_hin[nn] = df.iloc[reihe_hin[nn], 3]
                            else:
                                lon_st_hin[nn] = df.iloc[reihe_hin[nn], 1]
                                lon_sp_hin[nn] = df.iloc[reihe_hin[nn], 0]
                                lat_st_hin[nn] = df.iloc[reihe_hin[nn], 3]
                                lat_sp_hin[nn] = df.iloc[reihe_hin[nn], 2]
                        testvec = np.zeros(len(laye_r))                     # back
                        dito = 0
                        for nn in range(1, len(laye_r)):
                            if nn / 2 == np.round(nn / 2):
                                dito = dito + 3
                            else:
                                dito = dito + 1
                            testvec[nn] = dito
                        for nn in range(0, len(reihe_her)):
                            if len(laye_r) - 1 in testvec:
                                if nn / 2 != np.round(nn / 2):
                                    lon_st_her[nn] = df.iloc[reihe_her[nn], 1]
                                    lon_sp_her[nn] = df.iloc[reihe_her[nn], 0]
                                    lat_st_her[nn] = df.iloc[reihe_her[nn], 3]
                                    lat_sp_her[nn] = df.iloc[reihe_her[nn], 2]
                                else:
                                    lon_st_her[nn] = df.iloc[reihe_her[nn], 0]
                                    lon_sp_her[nn] = df.iloc[reihe_her[nn], 1]
                                    lat_st_her[nn] = df.iloc[reihe_her[nn], 2]
                                    lat_sp_her[nn] = df.iloc[reihe_her[nn], 3]
                            else:
                                if nn / 2 != np.round(nn / 2):
                                    lon_st_her[nn] = df.iloc[reihe_her[nn], 0]
                                    lon_sp_her[nn] = df.iloc[reihe_her[nn], 1]
                                    lat_st_her[nn] = df.iloc[reihe_her[nn], 2]
                                    lat_sp_her[nn] = df.iloc[reihe_her[nn], 3]
                                else:
                                    lon_st_her[nn] = df.iloc[reihe_her[nn], 1]
                                    lon_sp_her[nn] = df.iloc[reihe_her[nn], 0]
                                    lat_st_her[nn] = df.iloc[reihe_her[nn], 3]
                                    lat_sp_her[nn] = df.iloc[reihe_her[nn], 2]
                        new_lat_st = np.concatenate((lat_st_hin, lat_st_her), axis=0)
                        new_lat_sp = np.concatenate((lat_sp_hin, lat_sp_her), axis=0)
                        new_lon_st = np.concatenate((lon_st_hin, lon_st_her), axis=0)
                        new_lon_sp = np.concatenate((lon_sp_hin, lon_sp_her), axis=0)
                        
                        #### flip WE
                        if self.dlg.checkBox_flipWE.isChecked():
                            new_lat_st = np.concatenate((lat_sp_hin, lat_sp_her), axis=0)
                            new_lat_sp = np.concatenate((lat_st_hin, lat_st_her), axis=0)
                            new_lon_st = np.concatenate((lon_sp_hin, lon_sp_her), axis=0)
                            new_lon_sp = np.concatenate((lon_st_hin, lon_st_her), axis=0)
                        arrays = np.transpose([new_lon_st, new_lon_sp, new_lat_st, new_lat_sp])
                        df = pd.DataFrame(arrays)

                    #### just turn over one side (e.g. Littorina towing)
                    elif self.dlg.Littorina.isChecked():
                        lis_t = list(range(0, len(laye_r)));
                        odds_idx = lis_t[1::2];
                        evens_idx = lis_t[::2]
                        vec = np.zeros(len(laye_r))
                        vec[odds_idx] = odds_idx
                        vec[evens_idx] = np.add(evens_idx, 2).tolist()
                        vec[1:] = np.add(vec[1:], -1).tolist()
                        vec[0] = vec[0] - 1
                        if len(laye_r) / 2 != np.round(len(laye_r) / 2):
                            vec[len(vec) - 1] = vec[len(vec) - 1] - 1
                        new_lon_st = np.zeros(len(df))
                        new_lon_sp = np.zeros(len(df))
                        new_lat_st = np.zeros(len(df))
                        new_lat_sp = np.zeros(len(df))
                        new_lon_st[odds_idx] = df.iloc[vec[odds_idx], 0]
                        new_lon_sp[odds_idx] = df.iloc[vec[odds_idx], 1]
                        new_lat_st[odds_idx] = df.iloc[vec[odds_idx], 2]
                        new_lat_sp[odds_idx] = df.iloc[vec[odds_idx], 3]
                        new_lon_st[evens_idx] = df.iloc[vec[evens_idx], 1]
                        new_lon_sp[evens_idx] = df.iloc[vec[evens_idx], 0]
                        new_lat_st[evens_idx] = df.iloc[vec[evens_idx], 3]
                        new_lat_sp[evens_idx] = df.iloc[vec[evens_idx], 2]
                        
                        #### flip WE cumbersome and double
                        if self.dlg.checkBox_flipWE.isChecked():
                            new_lat_st2 = new_lat_sp
                            new_lat_sp2 = new_lat_st
                            new_lon_st2 = new_lon_sp
                            new_lon_sp2 = new_lon_st
                            new_lat_st = new_lat_st2
                            new_lat_sp = new_lat_sp2
                            new_lon_st = new_lon_st2
                            new_lon_sp = new_lon_sp2
                        arrays = np.transpose([new_lon_st, new_lon_sp, new_lat_st, new_lat_sp])
                        df = pd.DataFrame(arrays)

                else:
                    print("track not manipulated")

                #### #### #### #### make just two culumns Lon and Lat #### #### #### #### #### #### #### #### #### #### #### ####
                lis_t2 = list(range(0, len(df.index) * 2))
                odds_idx2 = lis_t2[1::2]
                evens_idx2 = lis_t2[::2]
                Lon = np.zeros(len(df.index) * 2)
                Lon[odds_idx2] = df[0]
                Lon[evens_idx2] = df[1]
                Lat = np.zeros(len(df.index) * 2)
                Lat[odds_idx2] = df[2]
                Lat[evens_idx2] = df[3]

                if self.dlg.normalProfiles.isChecked():
                    Lon_organised = np.zeros(len(df) * 2)
                    Lat_organised = np.zeros(len(df) * 2)
                    for mm in list(range(0, len(df) * 2)):
                        Lon_organised[mm] = Lon[int(idx_reihe[mm])]
                        Lat_organised[mm] = Lat[int(idx_reihe[mm])]
                    Lon = Lon_organised
                    Lat = Lat_organised

                #### flip WE for in general no further track manupulation
                if self.dlg.checkBox_flipWE.isChecked():
                    idx_reihe = -1 + np.sort(np.matlib.repmat(np.arange(0, len(laye_r) * 2, 4).tolist(), 1, 4)) + np.matlib.repmat((2, 1, 4, 3), 1, len(np.arange(0, len(laye_r) * 2, 4).tolist()))
                    idx_reihe = idx_reihe[0][:];  # len(idx_reihe) # idx_reihe.tolist()
                    idx_reihe = idx_reihe[0:len(df) * 2]
                    Lon_organised = np.zeros(len(df) * 2)
                    Lat_organised = np.zeros(len(df) * 2)
                    for mm in range(0, len(df) * 2):
                        Lon_organised[mm] = Lon[int(idx_reihe[mm])]
                        Lat_organised[mm] = Lat[int(idx_reihe[mm])]
                    Lon = Lon_organised
                    Lat = Lat_organised

                #### #### #### #### plot the track to check the track #### #### #### #### #### #### #### #### #### #### #### ####
                plt.figure(4)
                plt.plot(Lon, Lat, label="track")
                plt.plot(Lon[0], Lat[0], 'r*', label="start")
                plt.ylabel('Lat')
                plt.xlabel('Lon')
                plt.legend(loc="upper left")
                plt.show()
                
            elif Point_MPoint_Line==0:   #### #### run through stations most efficiently (traveling salesman problem approach)
                layer_provider.addAttributes([QgsField("X",QVariant.Double),
                QgsField("Y",QVariant.Double)])
                laye_r.updateFields()
                laye_r.startEditing()
                
                for fea_t in laye_r.getFeatures():
                    geom = fea_t.geometry().asPoint()  # MultiPoint noch extra abdecken
                    fea_t["X"] = geom[0]
                    fea_t["Y"] = geom[1]
                    laye_r.updateFeature(fea_t)
                laye_r.commitChanges()
                
                df=pd.DataFrame(fea_t.attributes() for fea_t in laye_r.getFeatures(QgsFeatureRequest()))
    
                def tsp_nn(stations_xy): #### #### quick transferred from % Author: Joseph Kirk % Email: jdkirk630@gmail.com #### ####
                    stations = list(range(0, np.size(stations_xy,0))) #### simple implementation of traveling salesman problem by nearest neighbour
                    xv,yv = np.meshgrid(stations,stations)
                    dist_mat=np.square(stations_xy.iloc[xv.flatten()].to_numpy()-stations_xy.iloc[yv.flatten()].to_numpy()) # attention: tsp nearest neighbour using lat lon (for relative idx in our lat ok)
                    dist_mat=np.sqrt(dist_mat.sum(1))
                    dist_mat=np.reshape(dist_mat, (len(stations),len(stations)))
                    
                    """
                    def extents(f):
                      delta = f[1] - f[0]
                      return [f[0] - delta/2, f[-1] + delta/2]
                      
                    plt.imshow(dist_mat, aspect='auto', interpolation='none',
                           extent=extents(stations) + extents(stations), origin='lower')
                    plt.show()
                    """
                    
                    pop = np.zeros((len(stations),len(stations)))
                    optimal_distances_vec=np.zeros(len(stations))
                    
                    for nn in list(range(0,len(optimal_distances_vec))):
                        d=0
                        thisRte = np.zeros(len(stations))
                        visited = np.zeros(len(stations))
                        I=nn
                        visited[I] = 1
                        thisRte[1] = I
                        
                        for mm in list(range(0,len(stations)-1)):
                            dists = dist_mat[I,:]
                            dists[visited==1] = np.nan # manipulating the vector derived from an array changes here the array wtf, no idea why, yet -> dump but for now define dist_mat new
                            J = np.nanargmin(dists)
                            visited[J] = 1
                            thisRte[mm+1] = J
                            d = d + dist_mat[I,J]
                            I = J
                            dist_mat=np.square(stations_xy.iloc[xv.flatten()].to_numpy()-stations_xy.iloc[yv.flatten()].to_numpy())
                            dist_mat=np.sqrt(dist_mat.sum(1))
                            dist_mat=np.reshape(dist_mat, (len(stations),len(stations)))
                            
                        d = d + dist_mat[I,nn]
                        pop[nn,:] = thisRte
                        optimal_distances_vec[nn] = d
                    
                    optRoute = pop[optimal_distances_vec.argmin()]
                    return optRoute
                
                station_order=tsp_nn(df)
                station_order=station_order.tolist()
                
                Lon = df.iloc[station_order,0]
                Lat = df.iloc[station_order,1]
                
                #### plot the track to check the track
                plt.figure(4)
                plt.plot(Lon,Lat, label="track")
                plt.plot(Lon,Lat,'r*', label="stations")
                plt.ylabel('Lat'); plt.xlabel('Lon')
                plt.legend()
                plt.show()
            
            #### #### #### #### make DD MM.MMMMM #### #### #### #### #### #### #### #### #### #### #### ####
            #### make DD MM.MMMMM for transas
            DD_lon = np.floor(Lon); DD_lat = np.floor(Lat)
            DM_lon = np.array(Lon - DD_lon) * 60; DM_lat = np.array(Lat - DD_lat) * 60;
            WP = range(1, len(Lon)+1)
            data_arra_y = np.array([WP, DD_lon, DM_lon, DD_lat, DM_lat])
            data_fram_e = pd.DataFrame(data_arra_y)

            ####

            def fprintf_copy(stream, format_spec, *args):
                stream.write(format_spec % args)

            #### #### #### #### #### #### #### 
            #### make format and export file
            now = datetime.now()
            datestring=now.strftime("%d/%m/%Y %H:%M:%S")


            filename = self.dlg.le_outTrack.text()
            original_stdout = sys.stdout # Save a reference to the original standard output
            
            with open(filename, "a") as f_out:
                f_out.seek(0)
                f_out.truncate()
                f_out.write(os.path.join(";Route track", datestring) + "\n")
                f_out.close
                
            with open(filename, "a") as f_out:
                
                sys.stdout = f_out  # Change the standard output to the file we created.
                print( ''.join(str(fprintf_copy(sys.stdout,
                                 ";\nWP %03.f NAME\nLAT  %.f°%.5f LON  %.f°%.5f\nRL (Rumb Line)\nXTE= 0.00nm\nTurnRadius= 0.00nm\n"
                                 , data_fram_e.iloc[0, waypoint], data_fram_e.iloc[3, waypoint]
                                 , data_fram_e.iloc[4, waypoint], data_fram_e.iloc[1, waypoint]
                                 , data_fram_e.iloc[2, waypoint]) ) for waypoint in
                                list(range(0, 10))) )
                sys.stdout = original_stdout  # Reset the standard output to its original value



                