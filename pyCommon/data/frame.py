from    ..either                    import core             as either
from    sklearn.feature_extraction  import DictVectorizer
from    sklearn                     import preprocessing
import  pandas                                              as pd
import  numpy                                               as np
import  training                                            as training

def _failIf(cond, errMessage):
    return lambda _: either.Left(errMessage) if cond \
            else either.Right(cond)


class Frame(object):
    '''
    wrapper around a pandas data frame

    df : pandas data frame
    '''

    def __init__(self,
                 df  = None):
        '''
        initialize
        '''
        self._df                    = df
        self._views                 = {}
        self._trainingSets          = {}


    def loadCsv(self,
                path):
        '''
        load underlying data frame with a csv.
        '''
        try:
            self._df = pd.read_csv(path)
            return either.Right({ path: path })
        except:
            return either.Left('failed to loadCsv')


    def loadPandas(self,
                   df):
        '''
        load underlying data frame a pandas data frame.
        '''
        self._df = df
        return either.Right('ok')


    def getFrame(self):
        '''
        safely get the underlying data frame
        '''
        if self._df is None:
            return either.Left('no frame loaded')
        else:
            return either.Right(self._df)


    def transformType(self,
                      col,
                      newType,
                      view   = None):
        '''
        transform the data type of a specified column
        '''
        return either.pipe(
            _failIf(self._df is None,
                'no frame loaded'
            ),
            lambda _: self._transformTypeUNSAFE(col, newType, view=view)
        )(None)


    def createView(self,
                   viewName,
                   query       = [],
                   overwrite   = True):
        '''
        create a named view of the frame
        '''
        return either.pipe(
            _failIf(not overwrite and viewName in self._views,
                'cannot overwrite existing view'
            ),
            _failIf(type(query) is not list,
                'sub view query must be a list'
            ),
            _failIf(len(query) == 0,
                'sub view must be constructed with a query'
            ),
            lambda _: self._createViewUNSAFE(viewName, query)
        )(None)


    def createRegressionSet(self,
                            setName,
                            predictors  = None,
                            responder   = None,
                            view        = None):
        '''
        create a named training set for a regression model using the data set
        itself or some named subview of it

        TODO: check if responder column is quantitative
        '''
        return either.pipe(
            _failIf(self._df is None,
                'no frame loaded'
            ),
            _failIf(predictors is None,
                'no predictors given'
            ),
            _failIf(responder is None,
                'no responder given'
            ),
            lambda _: self._createRegressionSetUNSAFE \
                    (setName, predictors, responder, view=view)
        )(None)


    def createClassificationSet(self,
                                setName,
                                predictors  = None,
                                responder   = None,
                                view        = None):
        '''
        create a named training set for a classification model using the data
        set itself or some named subview of it
        '''
        return either.pipe(
            _failIf(self._df is None,
                'no frame loaded'
            ),
            _failIf(predictors is None,
                'no predictors given'
            ),
            _failIf(responder is None,
                'no responder given'
            ),
            lambda _: self._createClassificationSetUNSAFE \
                    (setName, predictors, responder, view=view)
        )(None)


    def asDictListExclude(self,
                          exclude   = []):
        '''
        create a list of dictionaries from the underlying data frame. exclude
        the column names specified

        exclude : [string]
        '''
        return either.pipe(
            _failIf(self._df is None,
                'no frame loaded'
            ),
            lambda _: self._asDictListExcludeUNSAFE(exclude)
        )(None)


    def asDictListKeep(self,
                       keep     = []):
        '''
        create a list of dictionaries from the underlying data frame. keep
        the column names specified

        keep : [string]
        '''
        return either.pipe(
            _failIf(self._df is None,
                'no frame loaded'
            ),
            lambda _: self._asDictListKeepUNSAFE(keep)
        )(None)


    #####################################################################
    ##### UNSAFE METHODS: USED PRIMARILY AS HELPER FUNCTIONS ############
    #####################################################################


    def _transformTypeUNSAFE(self,
                             col,
                             newType,
                             view   = None):
        '''
        UNSAFE: helper method for transformType
        '''
        if view is not None and view in self._views:
            return self._views[view].transformType(col, newType)
        else:
            try:
                self._df[col] = self._df[col].astype(newType)
                return either.Right('ok')
            except:
                return either.Left('failed to transform type')


    def _createViewUNSAFE(self,
                          viewName,
                          query):
        '''
        UNSAFE: helper method for createView
        '''
        qres = query[0](self._df) if len(query) == 1 \
            else either.pipe(*query)(self._df)

        if qres.name is 'Left':
            return either.Left('failed to create view')
        else:
            self._views[viewName] = Frame(qres.val)
            return either.Right('ok')


    def _createRegressionSetUNSAFE(self,
                                   setName,
                                   predictors,
                                   responder,
                                   view     = None):
        '''
        UNSAFE: helper method for createRegressionSet
        '''
        if view is not None and view in self._views:
            return self._views[view] \
                .createRegressionSet(setName, predictors, responder)
        else:
            predictorData = self.asDictListKeep(keep=predictors)
            responderData = self._df[responder].values
            trainingSet   = training.RegressionTrainingSet(
                predictors=predictors,
                responder=responder
            )

            if predictorData.name == 'Left':
                return either.Left('failed to create predictor set')

            loadStatus = trainingSet.loadData(predictorData.val, responderData)

            if loadStatus.name == 'Left':
                return either.Left('failed to load training set')

            # TODO: check overwrites
            self._trainingSets[setName] = trainingSet
            return either.Right('ok')


    def _createClassificationSetUNSAFE(self,
                                       setName,
                                       predictors,
                                       responder,
                                       view    = None):
        '''
        UNSAFE: helper method for createClassificationSet
        '''
        if view is not None and view in self._views:
            return self._views[view] \
                .createClassificationSet(setName, predictors, responder)
        else:
            predictorData = self.asDictListKeep(keep=predictors)
            responderData = self._df[responder].values
            trainingSet   = training.ClassificationTrainingSet(
                predictors=predictors,
                responder=responder
            )

            if predictorData.name == 'Left':
                return either.Left('failed to create predictor set')

            loadStatus = trainingSet.loadData(predictorData.val, responderData)

            if loadStatus.name == 'Left':
                return either.Left('failed to load training set')

            # TODO: check overwrites
            self._trainingSets[setName] = trainingSet
            return either.Right('ok')


    def _asDictListExcludeUNSAFE(self,
                                 exclude):
        '''
        UNSAFE: helper method for asDictListExclude

        TODO: find out why values lin models are different when this
        implementation is used:

        results = self._df.drop(exclude, axis=1).T.to_dict().values()
        '''
        keeps, toZip = [], []
        colVals = self._df.columns.values
        for i in np.arange(0, len(colVals)):
            if colVals[i] not in exclude:
                keeps.append(colVals[i])
                toZip.append(self._df.ix[:,i].values)

        return either.Right(
            map(lambda x: dict(zip(keeps, x)), zip(*toZip))
        )


    def _asDictListKeepUNSAFE(self,
                              keep):
        '''
        UNSAFE: helper method for asDictListKeep

        TODO: find out why values lin models are different when this
        implementation is used:

        results = self._df[keep].T.to_dict().values()
        '''
        keeps, toZip = [], []
        colVals = self._df.columns.values
        for i in np.arange(0, len(colVals)):
            if colVals[i] in keep:
                keeps.append(colVals[i])
                toZip.append(self._df.ix[:,i].values)

        return either.Right(
            map(lambda x: dict(zip(keeps, x)), zip(*toZip))
        )