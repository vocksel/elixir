-- ClassName: LocalScript

local replicatedStorage = game:GetService("ReplicatedStorage")
local nevermore = require(replicatedStorage:WaitForChild("NevermoreEngine"))

local player = game.Players.LocalPlayer

-- The splash screen has to be removed manually, otherwise it will stay
-- on-screen indefinitely.
nevermore.ClearSplash()

print("Hello "..player.Name.."!")
