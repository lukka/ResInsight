/////////////////////////////////////////////////////////////////////////////////
//
//  Copyright (C) 2017- Statoil ASA
// 
//  ResInsight is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
// 
//  ResInsight is distributed in the hope that it will be useful, but WITHOUT ANY
//  WARRANTY; without even the implied warranty of MERCHANTABILITY or
//  FITNESS FOR A PARTICULAR PURPOSE.
// 
//  See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html> 
//  for more details.
//
/////////////////////////////////////////////////////////////////////////////////

#include "RimEnsembleCurveSetCollection.h"

#include "RiaApplication.h"
#include "RiaColorTables.h"

#include "RifReaderEclipseSummary.h"

#include "RimProject.h"
#include "RimEnsembleCurveSet.h"
#include "RimSummaryCase.h"
#include "RimSummaryCrossPlot.h"
#include "RimSummaryCurve.h"
#include "RimSummaryPlot.h"
#include "RimSummaryPlotSourceStepping.h"
#include "RimSummaryCurveAppearanceCalculator.h"

#include "RiuLineSegmentQwtPlotCurve.h"
#include "RiuSummaryQwtPlot.h"

#include "cafPdmUiTreeViewEditor.h"

#include <QKeyEvent>

CAF_PDM_SOURCE_INIT(RimEnsembleCurveSetCollection, "RimEnsembleCurveSetCollection");

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
RimEnsembleCurveSetCollection::RimEnsembleCurveSetCollection()
{
    CAF_PDM_InitObject("Ensemble Curve Sets", ":/SummaryCurveFilter16x16.png", "", "");

    CAF_PDM_InitFieldNoDefault(&m_curveSets, "EnsembleCurveSets", "Ensemble Curve Sets", "", "", "");
    m_curveSets.uiCapability()->setUiHidden(true);
    m_curveSets.uiCapability()->setUiTreeChildrenHidden(false);

    CAF_PDM_InitField(&m_showCurves, "IsActive", true, "Show Curves", "", "", "");
    m_showCurves.uiCapability()->setUiHidden(true);

    //CAF_PDM_InitFieldNoDefault(&m_ySourceStepping, "YSourceStepping", "", "", "", "");
    //m_ySourceStepping = new RimSummaryPlotSourceStepping;
    //m_ySourceStepping->setSourceSteppingType(RimSummaryPlotSourceStepping::Y_AXIS);
    //m_ySourceStepping.uiCapability()->setUiHidden(true);
    //m_ySourceStepping.uiCapability()->setUiTreeChildrenHidden(true);
    //m_ySourceStepping.xmlCapability()->disableIO();

    //CAF_PDM_InitFieldNoDefault(&m_xSourceStepping, "XSourceStepping", "", "", "", "");
    //m_xSourceStepping = new RimSummaryPlotSourceStepping;
    //m_xSourceStepping->setSourceSteppingType(RimSummaryPlotSourceStepping::X_AXIS);
    //m_xSourceStepping.uiCapability()->setUiHidden(true);
    //m_xSourceStepping.uiCapability()->setUiTreeChildrenHidden(true);
    //m_xSourceStepping.xmlCapability()->disableIO();

    //CAF_PDM_InitFieldNoDefault(&m_unionSourceStepping, "UnionSourceStepping", "", "", "", "");
    //m_unionSourceStepping = new RimSummaryPlotSourceStepping;
    //m_unionSourceStepping->setSourceSteppingType(RimSummaryPlotSourceStepping::UNION_X_Y_AXIS);
    //m_unionSourceStepping.uiCapability()->setUiHidden(true);
    //m_unionSourceStepping.uiCapability()->setUiTreeChildrenHidden(true);
    //m_unionSourceStepping.xmlCapability()->disableIO();
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
RimEnsembleCurveSetCollection::~RimEnsembleCurveSetCollection()
{
    m_curveSets.deleteAllChildObjects();
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
bool RimEnsembleCurveSetCollection::isCurveSetsVisible()
{
    return m_showCurves();
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::loadDataAndUpdate(bool updateParentPlot)
{
    for (RimEnsembleCurveSet* curveSet : m_curveSets)
    {
        curveSet->loadDataAndUpdate(updateParentPlot);
    }

    //for (RimSummaryCurve* curve : m_curves)
    //{
    //    curve->loadDataAndUpdate(false);
    //    curve->updateQwtPlotAxis();
    //}

    //if ( updateParentPlot )
    //{
    //    RimSummaryPlot* parentPlot;
    //    firstAncestorOrThisOfTypeAsserted(parentPlot);
    //    if ( parentPlot->qwtPlot() )
    //    {
    //        parentPlot->qwtPlot()->updateLegend();
    //        parentPlot->updateAxes();
    //        parentPlot->updateZoomInQwt();
    //    }
    //}
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::setParentQwtPlotAndReplot(QwtPlot* plot)
{
    for (RimEnsembleCurveSet* curveSet : m_curveSets)
    {
        curveSet->setParentQwtPlotNoReplot(plot);
    }

    if (plot) plot->replot();
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::detachQwtCurves()
{
    for(const auto& curveSet : m_curveSets)
    {
        curveSet->detachQwtCurves();
    }
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::addCurveSet(RimEnsembleCurveSet* curveSet)
{
    static int nextAutoColorIndex = 1;
    static int numberOfColors = (int)RiaColorTables::summaryCurveDefaultPaletteColors().size();

    if (curveSet)
    {
        curveSet->setColor(RimSummaryCurveAppearanceCalculator::cycledPaletteColor(nextAutoColorIndex));
        m_curveSets.push_back(curveSet);

        nextAutoColorIndex = (++nextAutoColorIndex) % numberOfColors;
    }
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::deleteCurveSet(RimEnsembleCurveSet* curveSet)
{
    if (curveSet)
    {
        m_curveSets.removeChildObject(curveSet);
        delete curveSet;
    }
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
std::vector<RimEnsembleCurveSet*> RimEnsembleCurveSetCollection::curveSets() const
{
    return m_curveSets.childObjects();
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
std::vector<RimEnsembleCurveSet*> RimEnsembleCurveSetCollection::visibleCurveSets() const
{
    std::vector<RimEnsembleCurveSet*> visible;

    for (auto c : m_curveSets)
    {
        if (c->isCurvesVisible())
        {
            visible.push_back(c);
        }
    }

    return visible;
}

////--------------------------------------------------------------------------------------------------
///// 
////--------------------------------------------------------------------------------------------------
//void RimEnsembleCurveSetCollection::deleteCurvesAssosiatedWithCase(RimSummaryCase* summaryCase)
//{
//    std::vector<RimSummaryCurve*> summaryCurvesToDelete;
//
//    for (RimSummaryCurve* summaryCurve : m_curves)
//    {
//        if (!summaryCurve) continue;
//        if (!summaryCurve->summaryCaseY()) continue;
//
//        if (summaryCurve->summaryCaseY() == summaryCase)
//        {
//            summaryCurvesToDelete.push_back(summaryCurve);
//        }
//    }
//    for (RimSummaryCurve* summaryCurve : summaryCurvesToDelete)
//    {
//        m_curves.removeChildObject(summaryCurve);
//        delete summaryCurve;
//    }
//
//}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::deleteAllCurveSets()
{
    m_curveSets.deleteAllChildObjects();
}

////--------------------------------------------------------------------------------------------------
///// 
////--------------------------------------------------------------------------------------------------
//void RimEnsembleCurveSetCollection::updateCaseNameHasChanged()
//{
//    for (RimSummaryCurve* curve : m_curves)
//    {
//        curve->updateCurveNameNoLegendUpdate();
//        curve->updateConnectedEditors();
//    }
//
//    RimSummaryPlot* parentPlot;
//    firstAncestorOrThisOfTypeAsserted(parentPlot);
//    if (parentPlot->qwtPlot()) parentPlot->qwtPlot()->updateLegend();
//}
//
////--------------------------------------------------------------------------------------------------
///// 
////--------------------------------------------------------------------------------------------------
//void RimEnsembleCurveSetCollection::setCurrentSummaryCurve(RimSummaryCurve* curve)
//{
//    m_currentSummaryCurve = curve;
//
//    updateConnectedEditors();
//}
//
////--------------------------------------------------------------------------------------------------
///// 
////--------------------------------------------------------------------------------------------------
//std::vector<caf::PdmFieldHandle*> RimEnsembleCurveSetCollection::fieldsToShowInToolbar()
//{
//    RimSummaryCrossPlot* parentCrossPlot;
//    firstAncestorOrThisOfType(parentCrossPlot);
//
//    if (parentCrossPlot)
//    {
//        return m_unionSourceStepping->fieldsToShowInToolbar();
//    }
//
//    return m_ySourceStepping()->fieldsToShowInToolbar();
//}
//
////--------------------------------------------------------------------------------------------------
///// 
////--------------------------------------------------------------------------------------------------
//void RimEnsembleCurveSetCollection::handleKeyPressEvent(QKeyEvent* keyEvent)
//{
//    if (!keyEvent) return;
//
//    RimSummaryPlotSourceStepping* sourceStepping = nullptr;
//    {
//        RimSummaryCrossPlot* summaryCrossPlot = nullptr;
//        this->firstAncestorOrThisOfType(summaryCrossPlot);
//        
//        if (summaryCrossPlot)
//        {
//            sourceStepping = m_unionSourceStepping();
//        }
//        else
//        {
//            sourceStepping = m_ySourceStepping();
//        }
//    }
//
//    if (keyEvent->key() == Qt::Key_PageUp)
//    {
//        if (keyEvent->modifiers() & Qt::ShiftModifier)
//        {
//            sourceStepping->applyPrevCase();
//
//            keyEvent->accept();
//        }
//        else if (keyEvent->modifiers() & Qt::ControlModifier)
//        {
//            sourceStepping->applyPrevOtherIdentifier();
//
//            keyEvent->accept();
//        }
//        else
//        {
//            sourceStepping->applyPrevQuantity();
//
//            keyEvent->accept();
//        }
//    }
//    else if (keyEvent->key() == Qt::Key_PageDown)
//    {
//        if (keyEvent->modifiers() & Qt::ShiftModifier)
//        {
//            sourceStepping->applyNextCase();
//
//            keyEvent->accept();
//        }
//        else if (keyEvent->modifiers() & Qt::ControlModifier)
//        {
//            sourceStepping->applyNextOtherIdentifier();
//
//            keyEvent->accept();
//        }
//        else
//        {
//            sourceStepping->applyNextQuantity();
//
//            keyEvent->accept();
//        }
//    }
//}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::fieldChangedByUi(const caf::PdmFieldHandle* changedField, const QVariant& oldValue, const QVariant& newValue)
{
    if (changedField == &m_showCurves)
    {
        loadDataAndUpdate(true);
    }
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::defineUiOrdering(QString uiConfigName, caf::PdmUiOrdering& uiOrdering)
{
    //RimSummaryCrossPlot* parentCrossPlot;
    //firstAncestorOrThisOfType(parentCrossPlot);

    //if (parentCrossPlot)
    //{
    //    {
    //        auto group = uiOrdering.addNewGroup("Y Source Stepping");

    //        m_ySourceStepping()->uiOrdering(uiConfigName, *group);
    //    }

    //    {
    //        auto group = uiOrdering.addNewGroup("X Source Stepping");

    //        m_xSourceStepping()->uiOrdering(uiConfigName, *group);
    //    }

    //    {
    //        auto group = uiOrdering.addNewGroup("XY Union Source Stepping");

    //        m_unionSourceStepping()->uiOrdering(uiConfigName, *group);
    //    }
    //}
    //else
    //{
    //    auto group = uiOrdering.addNewGroup("Plot Source Stepping");

    //    m_ySourceStepping()->uiOrdering(uiConfigName, *group);
    //}
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
caf::PdmFieldHandle* RimEnsembleCurveSetCollection::objectToggleField()
{
    return &m_showCurves;
}

//--------------------------------------------------------------------------------------------------
/// 
//--------------------------------------------------------------------------------------------------
void RimEnsembleCurveSetCollection::defineObjectEditorAttribute(QString uiConfigName, caf::PdmUiEditorAttribute* attribute)
{
    //caf::PdmUiTreeViewEditorAttribute* myAttr = dynamic_cast<caf::PdmUiTreeViewEditorAttribute*>(attribute);
    //if (myAttr && m_currentSummaryCurve.notNull())
    //{
    //    myAttr->currentObject = m_currentSummaryCurve.p();
    //}
}