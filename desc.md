## 项目主要分为两个部分 **注册 googlevoice** 和 **发送短信**，发送是以组为单位，组名称取页面上的分组输入框的内容

### 1. 注册 googlevoice

1.  注册 googlevoice 界面上有两个输入框，一个输入分组名称，一个选择账号文件，两项有一项未输入都要在点击运行时提醒
2.  两项输入内容校验通过后，判断当前分组名称是否已经在运行，如果有已经在运行注册流程的分组名称，提示当前分组已运行，不可重复运行，如果没有，判断当前分组名是否存在，如果不存在程序终止运行，判断分组代码如下
```js
 const groupId = await getGroupIdByName(groupName)
    if (!groupId) {
        return
    }
```
3.  点击运行按钮开始运行脚本,首选读取本地账号文件内容(账号文件存储在 file/account/groupname.json,如果没有需创建)到数组中，然后解析选择的 excel 账号文件，生成新账号数组，然后过滤掉已存在于本地账号文件的账号(取二者的并集),然后重新写入到本地账号文件中去,相关代码如下

    ```js
    const accountInfoFileName = `./file/account_info/${groupName}.json`;
    const currentAccountInfoList = await getJsonFileInfo(accountInfoFileName);
    const excelFileName = `./file/excel_info/${groupName}.xlsx`;
    const newAccountInfo = getJsonFromExcel(excelFileName);
    newAccountInfo.forEach((account) => {
      //按用户名去重
      if (!currentAccountInfoList.find((item) => item.userName == account.userName)) {
        currentAccountInfoList.push(account);
      }
    });
    console.log(newAccountInfo);
    await writeJsonToFile(accountInfoFileName, currentAccountInfoList);
    ```
4. 读取完账号信息后开始创建窗口，首先读取本地窗口文件内容(窗口文件存储在file/window/groupname.json,如果没有需创建)到数组中，然后遍历上一步生成的账号信息，根据用户名和密码是否相同判断哪些账号需要创建窗口,然后生成请求参数，调用创建窗口的接口,如果创建成功，根据返回结果生成窗口信息，最后存储到本地窗口文件中,相关代码如下
    ```js
    //1.2.1 获取当前已有窗口信息
    const windowInfoFileName = `./file/window_info/${groupName}.json`;
    const currentWindowInfo = await getJsonFileInfo(windowInfoFileName);
    if (newAccountInfo && newAccountInfo.length > 0) {
        for (let i = 0; i < newAccountInfo.length; i++) {
        const accountInfo = newAccountInfo[i];
        if (!currentWindowInfo.find(item => item.userName === accountInfo.userName && item.password === accountInfo.password)) {
            //如果当前窗口信息中不包含当前账号，添加新的窗口
            const windowInfoParams = generateWindowInfo(
                groupId,
                "https://accounts.google.com/",
                "gmail",
                `${groupName}-${i}`,
                accountInfo.userName,
                accountInfo.password,
                accountInfo.remark,
                2,
                "socks5",
                accountInfo.host,
                accountInfo.port,
                accountInfo.proxyUserName,
                accountInfo.proxyPassword
            );
            const res = await createBrowser(windowInfoParams);
            if (res.success) {
            console.log("添加窗口成功！", windowInfoParams.userName);
            //1.3保存窗口信息
            const windowInfo = {
                id: res.data.id,
                seq: res.data.seq,
                code: res.data.code,
                groupId: res.data.groupId,
                platform: res.data.platform,
                platformIcon: res.data.platformIcon,
                name: res.data.name,
                userName: res.data.userName,
                password: res.data.password,
                proxyMethod: res.data.proxyMethod,
                proxyType: res.data.proxyType,
                host: res.data.host,
                port: res.data.port,
                proxyUserName: res.data.proxyUserName,
                proxyPassword: res.data.proxyPassword,
            }
            currentWindowInfo.push(windowInfo)
            } else {
            console.log("添加窗口失败！", windowInfoParams.userName)
            }
        }
        }
        await writeJsonToFile(windowInfoFileName, currentWindowInfo);
    }
    ```
5. 开始循环遍历窗口信息，打开窗口执行注册gv的操作,注册成功后更新窗口信息的相关字段，然后将窗口信息再次写入到文件中，相关代码如下
    ```js
    //开始循环遍历创建的窗口，打开窗口
        for (let i = 0; i < todayWindowInfoList.length; i++) {
            let isRunning = await checkIsRunning(configFileName)
            if (!isRunning) {
                console.log("用户停止程序")
                return
            }
            const currentWindow = todayWindowInfoList[i]
            if (!currentWindow.registerFailedInfo) {
                currentWindow.registerFailedInfo = []
            }
            const todayFailedInfo = currentWindow.registerFailedInfo.find(item => item.date === dateStr)
            if (todayFailedInfo && todayFailedInfo.count > 3) {
                console.log(`今日注册失败次数超过3次,不再操作窗口${currentWindow.seq}`)
                continue
            }
            console.log(`开始操作窗口${currentWindow.seq}`)
            const openRes = await openWindow(currentWindow.id)
            if (openRes.success) {
                console.log('打开窗口成功')
                currentWindow.isOpenSuccess = true;
                const driver = getDriver(openRes)
                // await toGVTab(driver)
                driver.get('https://voice.google.com/')
                const isSuccess = await loginToGV(driver, currentWindow.userName, currentWindow.password, currentWindow.remark)
                if (isSuccess) {
                    console.log('gv注册成功,窗口id:', currentWindow.seq)
                    currentWindow.isRegisterSuccess = true
                } else {
                    console.log('gv注册失败,窗口id:', currentWindow.seq)
                    currentWindow.isRegisterSuccess = false
                    if (todayFailedInfo) {
                        todayFailedInfo.count = todayFailedInfo.count + 1
                    } else {
                        currentWindow.registerFailedInfo.push({
                            date: date, count: 1
                        })
                    }
                }
                await closeAllTab(driver)
            } else {
                console.log('打开窗口失败')
                currentWindow.isOpenSuccess = false;
                if (todayFailedInfo) {
                    todayFailedInfo.count = todayFailedInfo.count + 1
                } else {
                    currentWindow.registerFailedInfo.push({
                        date: date, count: 1
                    })
                }
            }
            await writeJsonToFile(todayWindowListFile, todayWindowInfoList);
            await delayed(2000)
            try {
                const service = chrome.getDefaultService()
                if (service) {
                    await service.kill()
                    await delayed(2000)
                }
                if (!currentWindow.hasUnreadMsg) {
                    await closeBrowser(currentWindow.id)
                }
            } catch (e) {
                console.log('关闭窗口失败', e)
            }
            isRunning = await checkIsRunning(configFileName)
            if (!isRunning) {
                console.log("用户停止程序")
                return
            }
        }
    ```

### 2. 发送短信 
