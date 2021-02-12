import datetime
import re
from datetime import datetime, time

import discord
import sqlalchemy
from discord.ext import commands
from pytz import timezone

from db.models import session_creator, EmployeeHours


class HeathCog(commands.Cog, name="Health"):

    def __init__(self, bot):
        self.bot = bot
        self.session = session_creator()

    @commands.command(name="setstarttime", aliases=['start', 'setstart', 'set_start_time'], brief='example: e~setstarttime 8:30 AM PST')
    async def set_start_time(self, ctx: discord.ext.commands.Context, time, am_pm, timezone):
        check = re.split('[-:]', time)
        if len(check) != 2 or int(check[0]) > 12 or int(check[1]) > 59:
            await ctx.send("Time input is invalid, please check again.")
            return
        if am_pm.lower() != "am" and am_pm.lower() != "pm":
            await ctx.send("AM/PM input is invalid, please check again.")
            return
        session = session_creator()
        employee = session.query(EmployeeHours).filter_by(discordId=str(ctx.author.id)).first()
        if not employee:
            employee = EmployeeHours(discordId=str(ctx.author.id), active_start_time=f"{time} {am_pm} {timezone}")
            session.add(employee)
        else:
            employee.active_start_time = f"{time} {am_pm} {timezone}"
        try:
            session.commit()
            session.close()
        except sqlalchemy.exc.DataError:
            await ctx.send("Time format invalid... try checking your timezone.")
            return
        await ctx.send("Start time set! Make sure your end time is also set!")

    @commands.command(name="setendtime", aliases=['end', 'setend', 'set_end_time'], brief='example: e~setendtime 10:30 PM PST')
    async def set_end_time(self, ctx: discord.ext.commands.Context, time, am_pm, timezone):
        check = re.split('[-:]', time)
        if len(check) != 2 or int(check[0]) > 12 or int(check[1]) > 59:
            await ctx.send("Time input is invalid, please check again.")
            return
        if am_pm.lower() != "am" and am_pm.lower() != "pm":
            await ctx.send("AM/PM input is invalid, please check again.")
            return

        session = session_creator()
        employee = session.query(EmployeeHours).filter_by(discordId=str(ctx.author.id)).first()
        if not employee:
            employee = EmployeeHours(discordId=str(ctx.author.id), active_end_time=f"{time} {am_pm} {timezone}")
            session.add(employee)
        else:
            employee.active_end_time = f"{time} {am_pm} {timezone}"
        try:
            session.commit()
            session.close()
        except sqlalchemy.exc.DataError:
            await ctx.send("Time format invalid... try checking your timezone.")
            return
        await ctx.send("End time set! Make sure your start time is also set!")

    @commands.command(name="setdays", aliases=['set_days'], brief='Set working days.')
    async def set_days(self, ctx: discord.ext.commands.Context, *, days):
        valid_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        days = days.title().split(" ")
        for day in days:
            if day not in valid_days:
                await ctx.send("I couldn't parse one of your days. Please check and try again.\nValid days are: "
                               "Sun, Mon, Tue, Wed, Thu, Fri, Sat")
                return
        session = session_creator()
        employee = session.query(EmployeeHours).filter_by(discordId=str(ctx.author.id)).first()
        if not employee:
            employee = EmployeeHours(discordId=str(ctx.author.id), days=" ".join(days))
            session.add(employee)
        else:
            employee.days = " ".join(days)
        session.commit()
        session.close()
        await ctx.send("Days set! Make sure your start and end times are also set!")

    @commands.command(name="howtouse", aliases=['how_to_use'], brief='explains how to use this very user friendly bot.')
    async def how_to_use(self, ctx: discord.ext.commands.Context):
        await ctx.send("""1) use 'e~setstarttime' ex: 'e~setstarttime 8:30 AM PST'
2) use 'e~setendtime' ex: 'e~setendtime 10:00 PM PST'
3) verify your hours are correct by doing 'e~hours'
4) profit 🚀.""")

    @commands.command(name="activehours", aliases=['hours', 'time', 'active_hours'], brief='Show what hours you have set.')
    async def active_hours(self, ctx: discord.ext.commands.Context):
        session = session_creator()
        employee = session.query(EmployeeHours).filter_by(discordId=str(ctx.author.id)).first()
        if employee and (employee.active_start_time or employee.active_end_time):
            out_message = ""
            if employee.active_start_time:
                startTime = time.fromisoformat(str(employee.active_start_time))
                out_message += f"Start Time: {startTime.strftime('%I:%M:%S %p %Z')}"
            if employee.active_end_time:
                endTime = time.fromisoformat(str(employee.active_end_time))
                out_message += f"\nEnd Time: {endTime.strftime('%I:%M:%S %p %Z')}"
            out_message += f"\nEnabled: {employee.enabled}\nDays: {employee.days}"
            await ctx.send(out_message)
        else:
            await ctx.send("You don't have any hours set!")
        session.close()

    @commands.command(brief='Enable active hours (default).')
    async def enable(self, ctx: discord.ext.commands.Context):
        session = session_creator()
        employee = session.query(EmployeeHours).filter_by(discordId=str(ctx.author.id)).first()
        if employee and (employee.active_start_time or employee.active_end_time):
            employee.enabled = True
            await ctx.send("Active hours set to enabled.")
        else:
            await ctx.send("You haven't set up your hours yet!")
        session.commit()
        session.close()

    @commands.command(brief='Disable active hours.')
    async def disable(self, ctx: discord.ext.commands.Context):
        session = session_creator()
        employee = session.query(EmployeeHours).filter_by(discordId=str(ctx.author.id)).first()
        if employee and (employee.active_start_time or employee.active_end_time):
            employee.enabled = False
            await ctx.send("Active hours set to disabled.")
        else:
            await ctx.send("You haven't set up your hours yet!")
        session.commit()
        session.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if len(message.mentions) > 0 and message.author != self.bot.user:
            session = session_creator()
            result = session.query(EmployeeHours).filter_by(discordId=str(message.mentions[0].id)).first()
            session.close()
            if result and result.active_end_time and result.active_start_time and result.enabled:
                startTime = time.fromisoformat(str(result.active_start_time))
                endTime = time.fromisoformat(str(result.active_end_time))
                startCompare: datetime.datetime = timezone('UTC').localize(datetime.utcnow()).astimezone(
                    startTime.tzinfo) \
                    .time().replace(tzinfo=startTime.tzinfo)
                endCompare: datetime = timezone('UTC').localize(datetime.utcnow()).astimezone(endTime.tzinfo).time() \
                    .replace(tzinfo=startTime.tzinfo)
                days = result.days.split(" ")
                day = timezone('UTC').localize(datetime.utcnow()).astimezone(endTime.tzinfo).strftime("%a")
                if day not in days:
                    await message.reply("Hey there! I see you've tagged an employee, just wanted to let "
                                        "you know that they have indicated it is currently outside of "
                                        "their usual working hours, so it may be a little bit before "
                                        "they can get back to you. Thanks for your patience!")
                    return

                if startTime > startCompare or endTime < endCompare:
                    await message.reply("Hey there! I see you've tagged an employee, just wanted to let "
                                        "you know that they have indicated it is currently outside of "
                                        "their usual working hours, so it may be a little bit before "
                                        "they can get back to you. Thanks for your patience!")


def setup(bot):
    bot.add_cog(HeathCog(bot))
