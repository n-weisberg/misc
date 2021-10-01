import math
import random

import matplotlib.pyplot as plt
import numpy as np


class Property:
    def __init__(self):
        self.listed = False
        self.listedTime = 0
        self.value = 0
        self.owing = 0
        self.age = 0

        self.monthlyMarketRate = 0
        self.monthlyInterestRate = 0
        self.monthlyMortgage = 0

    def simulateMonth(self):
        """
        Simulates a single month for the property
        Increments the properties age and time listed
        Decrements the amount owing on the property
        Calculate the market growth on the property
        """
        self.age += 1
        if self.owing >= 0:
            self.owing -= self.calculatePrincipalPaid()
            if self.owing <= 0:
                self.owing = 0
        if self.listed:
            self.listedTime += 1
        else:
            self.value = self.value * (1 + self.monthlyMarketRate)

    def calculatePrincipalPaid(self):
        return self.monthlyMortgage - self.owing * self.monthlyInterestRate

    def refinance(self, homeEquityLoan):
        age = self.age
        startingMortgage = self.monthlyMortgage
        self.age = 0
        if homeEquityLoan:
            realizedEquity = self.value - self.owing
            self.owing = self.owing + 0.8 * (self.value - self.owing)
            self.monthlyMortgage = monthlyMortgageCostForProperty(self.owing / 1000, 0, self.monthlyInterestRate, 25)
            return 0.8 * realizedEquity, age, self.monthlyMortgage - startingMortgage
        else:
            self.monthlyMortgage = monthlyMortgageCostForProperty(self.owing / 1000, 0, self.monthlyInterestRate, 25)
            return 0, age, self.monthlyMortgage - startingMortgage


class Data:
    def __init__(self, mapper):

        self.term = 100
        self.holdTime = mapper["holdTime"]
        self.safety = mapper["safety"]
        self.additions = mapper["additions"]
        self.expenses = mapper["expenses"]
        self.income = mapper["income"]

        self.cost = mapper["cost"]
        self.down = mapper["down"]
        self.amortization = mapper["amortization"]
        self.rent = mapper["rent"]

        self.tax = mapper["tax"]
        self.management = mapper["management"]
        self.repairs = mapper["repairs"]
        self.insurance = mapper["insurance"]

        self.interest = mapper["interest"]
        self.occupancy = mapper["occupancy"]
        self.time = mapper["time"]
        self.maxDTI = mapper["maxDTI"]
        self.market = mapper["market"]
        self.growth = mapper["growth"]

        self.months = 300

        self.monthlyInterestRate = 0
        self.monthlyGrowthRate = 0
        self.monthlyMarketRate = 0

        self.properties = []
        self.cash = 0
        self.emergencyFund = 0
        self.DTI = 0
        self.month = 0

    def setMonthlyRates(self):
        self.monthlyInterestRate = calculateMonthlyInterestRate(self.interest)
        self.monthlyGrowthRate = calculateMonthlyInterestRate(self.growth)
        self.monthlyMarketRate = calculateMonthlyInterestRate(self.market)

    def tryToSell(self):
        """
        Attempts to sell any eligible properties
        Lists any properties that are ready to be listed
        Sells any listed properties that are ready to sell
        """
        for property in self.properties:
            if not property.listed and property.age >= self.holdTime * 12:
                property.listed = True
                property.listedTime = 0
                print("Month {}: List {} month old property for ${}".format(self.month, property.age, property.value))
            if property.listed and property.listedTime >= self.time:
                equity = property.value - property.owing
                self.cash += equity
                self.properties.remove(property)
                print("Month {}: Sell {} month old property for ${}".format(self.month, property.age, property.value))
        return

    def tryToRefinance(self):
        """
        Go through all the properties and check if any are eligible for refinance
        They are eligible if they are not listed and have been held longer than the mortgage term
        We get a home equity loan during refinance if it's advisable
        """
        for property in self.properties:
            if not property.listed and property.age >= self.term * 12:
                if self.shouldDoHomeEquityLoan(property):
                    realized, age, diff = property.refinance(True)
                    self.cash += realized
                    print("Month {}: Release ${} from {} month old property in home equity loan, raising mortgage "
                          "payment by ${} "
                          .format(self.month, realized, age, diff))
                else:
                    _, age, diff = property.refinance(False)
                    print("Month {}: Refinance {} month old property, lowering mortgage by ${}"
                          .format(self.month, age, diff))

    def tryToBuy(self):
        """
        Attempts to purchase property
        Purchases a property if DTI can remain below max and can afford monthly expenses for safety period
        Favours minimal down payments
        """
        currentDebt = sum(
            [self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in self.properties]) + self.expenses
        currentMonthlyIncome = (len(self.properties) * (self.occupancy / 100) * self.rent) + self.income / 12
        down, monthlyMortgage = self.minimumDown(currentDebt, currentMonthlyIncome)
        if down is not None and self.canAffordProperty(monthlyMortgage, down):
            property = Property()
            property.value = (self.cost * 1000)
            property.owing = (self.cost * 1000 * (1 - down / 100))
            property.monthlyMarketRate = self.monthlyMarketRate
            property.monthlyInterestRate = self.monthlyInterestRate
            property.monthlyMortgage = monthlyMortgage
            self.properties.append(property)
            self.cash -= (self.cost * 1000 * down / 100) + self.monthlyExpensesCostPerProperty(
                monthlyMortgage) * self.safety
            self.emergencyFund += self.monthlyExpensesCostPerProperty(monthlyMortgage) * self.safety
            print("Month {}: Purchase ${} property at {}% down"
                  .format(self.month, self.cost * 1000, down))
        return

    def minimumDown(self, currentMonthlyDebt, currentMonthlyIncome):
        """
        Finds the minimum down payment possible to purchase a property while
        remaining below the max DTI
        Returns (down payment as a percent, monthly mortgage payment)
        """
        down = self.down
        while True:
            if down > 100:
                return None, None
            potentialDTI = self.calculatePotentialDTI(currentMonthlyDebt, currentMonthlyIncome, down)
            if potentialDTI <= self.maxDTI:
                return down, monthlyMortgageCostForProperty(self.cost, down, self.monthlyInterestRate,
                                                            self.amortization)
            down += 1

    def canAffordProperty(self, monthlyMortgage, down, extra=0):
        """
        Checks if there is enough cash to afford the down payment and monthly expenses for the safety period
        """
        return self.cash + extra >= (self.cost * 1000 * down / 100) + \
               self.monthlyExpensesCostPerProperty(monthlyMortgage) * self.safety

    def buildReport(self):
        print()
        print("-----Month " + str(self.month) + " -----")
        print("     Properties:", len(self.properties))
        print("     Cash:", str(self.cash))
        print("     Equity:", str(sum([(p.value - p.owing) for p in self.properties])))
        print("     Emergency Fund:", str(self.emergencyFund))
        print("     Total Assets:",
              str(self.cash + sum([(p.value - p.owing) for p in self.properties]) + self.emergencyFund))
        print("     DTI:", str(self.DTI))
        print("     Revenue:", str(len(self.properties) * (self.occupancy / 100) * self.rent))
        print("     Debt:", str(sum([self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in self.properties])))
        print("     Cash Flow:", str((len(self.properties) * (self.occupancy / 100) * self.rent) -
                                     sum([self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in
                                          self.properties])))
        print()
        #
        # for property in self.properties:
        #     print("-----Property-----")
        #     print(property.value)
        #     print(property.owing)
        #     print(property.age)
        #     print(property.listed)
        #     print(property.listedTime)
        return

    def reset(self):
        while True:
            att = input("Which attribute do you want to change?:")
            if att == "":
                break
            if not hasattr(self, att):
                continue
            new = float(input("What do you want to change " + att + " to?:"))
            setattr(self, att, new)

        self.monthlyInterestRate = 0
        self.monthlyGrowthRate = 0
        self.monthlyMarketRate = 0
        self.properties = []
        self.cash = 0
        self.emergencyFund = 0
        self.DTI = 0
        self.month = 0
        self.setMonthlyRates()

    def simulateMonth(self):
        """
        Run a single month simulation
        1. Sell any eligible properties
        2. Refinance any eligible properties
        3. Buy property if eligible
        4. Trigger single month simulation for each property
        5. Calculate cash from monthly additions, rent, mortgages, expenses
        6. Calculate growth of cash and emergency fund
        7. Calculate new DTI
        """
        self.tryToSell()
        self.tryToRefinance()
        self.tryToBuy()
        for property in self.properties:
            property.simulateMonth()
        self.cash += self.additions
        self.cash -= sum([self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in self.properties])
        self.cash += (self.occupancy / 100) * self.rent * len([p for p in self.properties if not p.listed])
        self.cash = self.cash * (1 + self.monthlyGrowthRate)
        self.emergencyFund = self.emergencyFund * (1 + self.monthlyGrowthRate)
        self.DTI = calculateDTI(
            sum([self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in self.properties]) + self.expenses,
            (len(self.properties) * (self.occupancy / 100) * self.rent) + self.income / 12
        )
        return

    def monthlyExpensesCostPerProperty(self, monthlyMortgage):
        """
        Sum of monthly expenses for a property
        """
        return self.tax / 12 + self.insurance / 12 + self.repairs / 12 + self.management / 12 + monthlyMortgage

    def monthlyDebtPerProperty(self, monthlyMortgage):
        """
        Sum of monthly debts for a property (included in DTI)
        """
        return self.tax / 12 + self.insurance / 12 + monthlyMortgage

    def calculatePotentialDTI(self, debt, income, down):
        """
        Calculates the hypothetical DTI if a property is purchased at the given percent down
        """
        addedExpense = self.monthlyExpensesCostPerProperty(monthlyMortgageCostForProperty(
            self.cost, down, self.monthlyInterestRate, self.amortization))
        addedIncome = self.rent * self.occupancy / 100
        return calculateDTI(debt + addedExpense, income + addedIncome)

    def shouldDoHomeEquityLoan(self, _property):
        """
        Checks if it's advisable to do a home equity loan
        If the cash released from the refinance is enough to purchase another property
        while keeping DTI below max, it returns true
        """
        currentDebt = sum([self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in self.properties]) + \
                      self.expenses
        homeEquityDebt = monthlyMortgageCostForProperty(
            (_property.value - _property.owing)*0.8/1000, 0, _property.monthlyInterestRate, self.amortization)
        currentMonthlyIncome = (len(self.properties) * (self.occupancy / 100) * self.rent) + self.income / 12
        released = (_property.value - _property.owing)*0.8
        down, monthlyMortgage = self.minimumDown(currentDebt + homeEquityDebt, currentMonthlyIncome)
        return down is not None and self.canAffordProperty(monthlyMortgage, down, released)

    def results(self):
        return self.cash + sum([(p.value - p.owing) for p in self.properties]) + self.emergencyFund, \
               (len(self.properties) * (self.occupancy / 100) * self.rent) - \
               sum([self.monthlyExpensesCostPerProperty(p.monthlyMortgage) for p in self.properties])


def calculateDTI(debt, income):
    """
    Calculates Debt to Income ratio
    """
    if income == 0:
        return 0
    return (debt / income) * 100


def calculateMonthlyInterestRate(rate):
    """
    Calculates monthly interest rate from yearly interest rate
    """
    return (10 ** (math.log10(1 + (rate / 100)) / 12)) - 1


def monthlyMortgageCostForProperty(cost, down, monthlyRate, period):
    """
    Calculates the monthly mortgage payment for a property
    """
    return (cost * 1000 * (1 - down / 100)) * \
           (monthlyRate * ((1 + monthlyRate) ** (period * 12))) / \
           (((1 + monthlyRate) ** (period * 12)) - 1)


def runOnce(mainSet):
    data = Data(mainSet)
    data.setMonthlyRates()
    while True:
        if data.month > data.months:
            data.reset()
        if data.month % 12 == 0:
            data.buildReport()
        data.simulateMonth()
        data.buildReport()
        data.month += 1


def getCashFlow(set):
    data = Data(set)
    data.setMonthlyRates()
    while True:
        if data.month > data.months:
            return data.results()[1]
        data.simulateMonth()
        data.month += 1


def getTotalAssets(set):
    data = Data(set)
    data.setMonthlyRates()
    while True:
        if data.month > data.months:
            return data.results()[0]
        data.simulateMonth()
        data.month += 1


def getBenchMark(additions, growth, period):
    total = additions
    for _ in range(period):
        total = total * (1 + calculateMonthlyInterestRate(growth))
        total += additions
    return total


def runSimulation(mainSet, variables, cashFlow, volatility, showBenchmark):
    """
    Runs a simulation using the mean values in mainSet, 
    showing the effect of changing each variable down to 50% it's value up to 200% percent it's value.
    Adds/subtracts a random percent amount to each variable up to a max of volatility.
    cashflow is a boolean to determine whether to use cashflow on the y-axis or total assets
    showBenchmark is a boolean to determine whether to show line on graph representing the scenario
    of just investing money in market instead of real estate
    """
    xpoints = np.array([m / 100 for m in range(50, 200, 5)])
    for key in variables:
        yPointsHolder = []
        for j in range(1 if volatility == 0 else 5):
            yPoints = []
            tmpSet = {}
            for i in xpoints:
                for trial in mainSet:
                    tmpSet[trial] = mainSet[trial] * (1.0 - volatility/100 + random.randint(0, 2*volatility)/100)
                for _key in key:
                    tmpSet[_key[0]] = mainSet[_key[0]] * (i if _key[1] else 1/i)
                yPoints.append(getCashFlow(tmpSet) if cashFlow else getTotalAssets(tmpSet))
            yPointsHolder.append(yPoints)
        yPoints = []
        for i in range(len(xpoints)):
            total = 0
            for array in yPointsHolder:
                total += array[i]
            total = total / len(yPointsHolder)
            yPoints.append(total)
        ypoints = np.array(yPoints)
        plt.plot(xpoints, ypoints)
    if showBenchmark:
        benchMark = getBenchMark(mainSet["additions"], mainSet["growth"], 180)
        benchMark = benchMark * calculateMonthlyInterestRate(mainSet["growth"]) if cashFlow else benchMark
        plt.plot(xpoints, [benchMark for _ in xpoints])
        variables.append("benchMark")
    plt.legend(variables)
    plt.ylim(bottom=0)
    plt.show()


# Variables we want to graph. Changing a variable's sign to 0 will represent it's reciprocal when graphed.
# This is useful for comparing the relative effect of two inversely favourable variables.
# ie. How does a 10% increase in rent compare to a 10% decrease in management fees? Easier to compare visually when one of them is flipped.


# variables = [[("additions", 1)], [("tax", 1)], [("management", 1)], [("repairs", 1)], [("insurance", 1)],
#              [("holdTime", 1)], [("safety", 1)], [("interest", 1)], [("time", 1)], [("market", 1)],
#              [("growth", 1)], [("expenses", 1)], [("income", 1)], [("down", 1)], [("amortization", 0)],
#              [("maxDTI", 1)], [("occupancy", 1)], [("rent", 1)], [("cost", 1)]]

variables = [[("additions", 1)], [("tax", 1)], [("management", 1)], [("repairs", 1)], [("insurance", 1)],
             [("holdTime", 1)], [("safety", 1)], [("interest", 1)], [("time", 1)], [("market", 1)],
             [("growth", 1)], [("expenses", 1)], [("income", 1)], [("down", 1)], [("amortization", 0)]]

# Mean values to use for simulation
mainSet = {
    "term": 5.0,  # mortgage fixed rate term in years
    "holdTime": 5.0, # time to hold property 
    "safety": 6.0, # number of months safety buffer to save before next property
    "additions": 2000.0, # money added from outside source monthly
    "expenses": 1000.0, # personal expenses from outside sources (for DTI)
    "income": 60000.0, # personal annual income from outside sources (for DTI)
    "cost": 240.0,  # average cost of property (1000s)
    "down": 20.0,   # percent down payment
    "amortization": 25, # amortization period
    "rent": 2400.0, # average rent recieved per property
    "tax": 2400.0,  # average annual property tax per property
    "management": 2400.0, # average annual property managment cost per property
    "repairs": 2400,    # average annual repairs cost per property
    "insurance": 1200.0,    # average annual insurance cost per property
    "interest": 2.0,    # average annual interest rate
    "occupancy": 92,    # average occupancy rate
    "time": 6, # average time in months a property in listed before it sells
    "maxDTI": 45.0, # max DTI allowed by banks
    "market": 2,    # average annual housing market growth
    "growth": 8     # average annual stock market growth
    }


# Uncomment one of the two function calls below.
# runOnce runs the main set of variables, printing a report every month
# runSimulation runs the data multiple times, 
# using a range of 50% - 200% of the mean values in the main set, 
# with random volatility added/subtracted from the variables, and then graphs the variables
# Note that depending on the values set, this simulation can take a few minutes to run!

runOnce(mainSet)
# runSimulation(mainSet, variables, True, 1, True)
